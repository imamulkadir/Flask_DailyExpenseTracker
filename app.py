import os
import json
import datetime
import csv
from io import StringIO
from calendar import month_name
from flask import Flask, render_template, request, redirect, url_for, flash, make_response
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# Create Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "fallback_secret_key")

# ==== File-based Storage Functions ====
def load_data():
    """Load expense data from JSON file"""
    try:
        with open('expenses.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {"default": {}}
    except json.JSONDecodeError:
        app.logger.error("Error reading expenses.json")
        return {"default": {}}

def save_data(data):
    """Save expense data to JSON file"""
    try:
        with open('expenses.json', 'w') as f:
            json.dump(data, f, indent=2, default=str)
    except Exception as e:
        app.logger.error(f"Error saving data: {e}")

def get_user_data(user_id="default"):
    """Get all data for a specific user"""
    data = load_data()
    return data.get(user_id, {})

def load_categories():
    """Load categories from JSON file"""
    try:
        with open('categories.json', 'r') as f:
            categories = json.load(f)
            return categories if isinstance(categories, list) else ["Food", "Transport", "Entertainment", "Other"]
    except FileNotFoundError:
        # Create default categories file
        default_categories = [
            "Food & Dining", "Transportation", "Shopping", "Entertainment", 
            "Bills & Utilities", "Healthcare", "Travel", "Education", 
            "Groceries", "Gas", "Coffee", "Other"
        ]
        save_categories(default_categories)
        return default_categories
    except json.JSONDecodeError:
        return ["Food", "Transport", "Entertainment", "Other"]

def save_categories(categories):
    """Save categories to JSON file"""
    try:
        with open('categories.json', 'w') as f:
            json.dump(categories, f, indent=2)
    except Exception as e:
        app.logger.error(f"Error saving categories: {e}")

# ==== Routes ====
@app.route('/')
def index():
    """Main dashboard with expense entry form and recent expenses"""
    user_data = get_user_data()
    categories = load_categories()
    
    # Get today's expenses
    today = datetime.date.today().strftime("%Y-%m-%d")
    today_expenses = user_data.get(today, [])
    today_total = sum(expense['amount'] for expense in today_expenses)
    
    # Get recent expenses (last 10)
    recent_expenses = []
    for date in sorted(user_data.keys(), reverse=True):
        for expense in user_data[date]:
            expense_with_date = expense.copy()
            expense_with_date['date'] = date
            recent_expenses.append(expense_with_date)
        if len(recent_expenses) >= 10:
            break
    
    return render_template('index.html', 
                         today_expenses=today_expenses,
                         recent_expenses=recent_expenses[:10],
                         today_total=today_total,
                         today_date=today,
                         categories=categories)

@app.route('/add_expense', methods=['POST'])
def add_expense():
    """Add a new expense"""
    try:
        amount = float(request.form.get('amount', 0))
        category = request.form.get('category', '').strip()
        date_str = request.form.get('date', datetime.date.today().strftime("%Y-%m-%d"))
        
        if amount <= 0:
            flash('Amount must be greater than 0', 'error')
            return redirect(url_for('index'))
        
        if not category:
            flash('Category is required', 'error')
            return redirect(url_for('index'))
        
        # Load current data
        data = load_data()
        user_data = data.get("default", {})
        
        # Initialize date if it doesn't exist
        if date_str not in user_data:
            user_data[date_str] = []
        
        # Add expense
        expense = {
            'amount': amount,
            'category': category,
            'timestamp': datetime.datetime.now().isoformat()
        }
        user_data[date_str].append(expense)
        
        # Save updated data
        data["default"] = user_data
        save_data(data)
        
        # Add category to categories list if it's new
        categories = load_categories()
        if category not in categories:
            categories.append(category)
            save_categories(categories)
        
        flash(f'✅ Logged: ${amount:.2f} for {category}', 'success')
        
    except ValueError:
        flash('❌ Invalid amount. Please enter a valid number.', 'error')
    except Exception as e:
        app.logger.error(f"Error adding expense: {e}")
        flash('❌ Error adding expense. Please try again.', 'error')
    
    return redirect(url_for('index'))

@app.route('/summary')
def summary():
    """Show expense summaries with filtering options"""
    user_data = get_user_data()
    filter_type = request.args.get('filter', 'today')
    
    now = datetime.datetime.now()
    total = 0
    expenses = []
    title = ""
    
    if filter_type == 'today':
        today = now.strftime("%Y-%m-%d")
        expenses = user_data.get(today, [])
        for expense in expenses:
            expense['date'] = today
        total = sum(expense['amount'] for expense in expenses)
        title = f"Today's Expenses ({today})"
        
    elif filter_type == 'week':
        # Last 7 days
        for i in range(7):
            date = (now - datetime.timedelta(days=i)).strftime("%Y-%m-%d")
            day_expenses = user_data.get(date, [])
            for expense in day_expenses:
                expense['date'] = date
                expenses.append(expense)
        total = sum(expense['amount'] for expense in expenses)
        title = "This Week's Expenses"
        
    elif filter_type == 'month':
        # Current month
        current_month = now.strftime("%Y-%m")
        for date, day_expenses in user_data.items():
            if date.startswith(current_month):
                for expense in day_expenses:
                    expense['date'] = date
                    expenses.append(expense)
        total = sum(expense['amount'] for expense in expenses)
        title = f"{month_name[now.month]} {now.year} Expenses"
    
    # Sort expenses by date (newest first)
    expenses.sort(key=lambda x: x['date'], reverse=True)
    
    # Calculate category breakdown
    category_totals = {}
    for expense in expenses:
        category = expense['category']
        category_totals[category] = category_totals.get(category, 0) + expense['amount']
    
    return render_template('summary.html', 
                         expenses=expenses,
                         total=total,
                         title=title,
                         filter_type=filter_type,
                         category_totals=category_totals)

@app.route('/export_csv')
def export_csv():
    """Export expenses to CSV file"""
    try:
        user_data = get_user_data()
        
        # Create CSV data
        output = StringIO()
        writer = csv.writer(output)
        writer.writerow(["Date", "Amount", "Category"])
        
        # Write expenses
        for date, expenses in sorted(user_data.items()):
            for expense in expenses:
                writer.writerow([date, expense['amount'], expense['category']])
        
        # Create response
        output.seek(0)
        csv_content = output.getvalue()
        
        response = make_response(csv_content)
        response.headers['Content-Type'] = 'text/csv'
        response.headers['Content-Disposition'] = f'attachment; filename=expenses_{datetime.datetime.now().strftime("%Y%m%d")}.csv'
        
        return response
        
    except Exception as e:
        app.logger.error(f"Error exporting CSV: {e}")
        flash('❌ Error exporting data. Please try again.', 'error')
        return redirect(url_for('index'))

@app.route('/delete_expense', methods=['POST'])
def delete_expense():
    """Delete a specific expense"""
    try:
        date_str = request.form.get('date')
        category = request.form.get('category')
        amount = float(request.form.get('amount', 0))
        
        if not date_str:
            flash('Date is required', 'error')
            return redirect(request.referrer or url_for('index'))
        
        # Load current data
        data = load_data()
        user_data = data.get("default", {})
        
        if date_str in user_data:
            # Find and remove the expense
            expenses = user_data[date_str]
            for i, expense in enumerate(expenses):
                if (expense['category'] == category and 
                    expense['amount'] == amount):
                    expenses.pop(i)
                    break
            
            # Remove empty date entries
            if not expenses:
                del user_data[date_str]
            
            # Save updated data
            data["default"] = user_data
            save_data(data)
            flash('✅ Expense deleted successfully', 'success')
        else:
            flash('❌ Expense not found', 'error')
            
    except Exception as e:
        app.logger.error(f"Error deleting expense: {e}")
        flash('❌ Error deleting expense. Please try again.', 'error')
    
    return redirect(request.referrer or url_for('index'))

@app.route('/edit_expense/<path:expense_id>', methods=['GET', 'POST'])
def edit_expense(expense_id):
    """Edit a specific expense"""
    try:
        # Parse expense_id (format: date_index)
        date_str, index_str = expense_id.split('_')
        index = int(index_str)
        
        user_data = get_user_data()
        categories = load_categories()
        
        if date_str not in user_data or index >= len(user_data[date_str]):
            flash('❌ Expense not found', 'error')
            return redirect(url_for('index'))
        
        expense = user_data[date_str][index]
        
        if request.method == 'POST':
            # Update expense
            new_amount = float(request.form.get('amount', 0))
            new_category = request.form.get('category', '').strip()
            new_date_str = request.form.get('date', date_str)
            
            if new_amount <= 0:
                flash('Amount must be greater than 0', 'error')
                return render_template('edit_expense.html', expense=expense, 
                                     categories=categories, 
                                     expense_date=date_str,
                                     expense_id=expense_id)
            
            if not new_category:
                flash('Category is required', 'error')
                return render_template('edit_expense.html', expense=expense, 
                                     categories=categories, 
                                     expense_date=date_str,
                                     expense_id=expense_id)
            
            # Load fresh data
            data = load_data()
            user_data = data.get("default", {})
            
            # Remove old expense
            if date_str in user_data and index < len(user_data[date_str]):
                user_data[date_str].pop(index)
                if not user_data[date_str]:
                    del user_data[date_str]
            
            # Add updated expense to new date
            if new_date_str not in user_data:
                user_data[new_date_str] = []
            
            updated_expense = {
                'amount': new_amount,
                'category': new_category,
                'timestamp': datetime.datetime.now().isoformat()
            }
            user_data[new_date_str].append(updated_expense)
            
            # Add category if it's new
            categories = load_categories()
            if new_category not in categories:
                categories.append(new_category)
                save_categories(categories)
            
            # Save updated data
            data["default"] = user_data
            save_data(data)
            
            flash('✅ Expense updated successfully', 'success')
            return redirect(url_for('index'))
        
        return render_template('edit_expense.html', expense=expense, 
                             categories=categories, 
                             expense_date=date_str,
                             expense_id=expense_id)
        
    except Exception as e:
        app.logger.error(f"Error editing expense: {e}")
        flash('❌ Error editing expense. Please try again.', 'error')
        return redirect(url_for('index'))

@app.route('/categories')
def manage_categories():
    """Manage expense categories"""
    categories = load_categories()
    user_data = get_user_data()
    
    # Calculate category usage statistics
    category_stats = {}
    for category in categories:
        count = 0
        total = 0
        for date, expenses in user_data.items():
            for expense in expenses:
                if expense['category'] == category:
                    count += 1
                    total += expense['amount']
        category_stats[category] = {'count': count, 'total': total}
    
    return render_template('categories.html', 
                         categories=categories, 
                         category_stats=category_stats)

@app.route('/add_category', methods=['POST'])
def add_category():
    """Add a new category"""
    try:
        new_category = request.form.get('category', '').strip()
        
        if not new_category:
            flash('Category name is required', 'error')
            return redirect(url_for('manage_categories'))
        
        categories = load_categories()
        
        if new_category in categories:
            flash('Category already exists', 'warning')
            return redirect(url_for('manage_categories'))
        
        categories.append(new_category)
        save_categories(categories)
        
        flash(f'✅ Category "{new_category}" added successfully', 'success')
        
    except Exception as e:
        app.logger.error(f"Error adding category: {e}")
        flash('❌ Error adding category. Please try again.', 'error')
    
    return redirect(url_for('manage_categories'))

@app.route('/delete_category', methods=['POST'])
def delete_category():
    """Delete a category"""
    try:
        category_to_delete = request.form.get('category', '').strip()
        
        if not category_to_delete:
            flash('Category name is required', 'error')
            return redirect(url_for('manage_categories'))
        
        categories = load_categories()
        
        if category_to_delete not in categories:
            flash('Category not found', 'error')
            return redirect(url_for('manage_categories'))
        
        # Check if category is in use
        user_data = get_user_data()
        category_in_use = False
        for date, expenses in user_data.items():
            if any(expense['category'] == category_to_delete for expense in expenses):
                category_in_use = True
                break
        
        if category_in_use:
            flash(f'❌ Cannot delete "{category_to_delete}" - it\'s being used by existing expenses', 'error')
            return redirect(url_for('manage_categories'))
        
        categories.remove(category_to_delete)
        save_categories(categories)
        
        flash(f'✅ Category "{category_to_delete}" deleted successfully', 'success')
        
    except Exception as e:
        app.logger.error(f"Error deleting category: {e}")
        flash('❌ Error deleting category. Please try again.', 'error')
    
    return redirect(url_for('manage_categories'))

@app.route('/analytics')
def analytics():
    """Show data visualization and analytics"""
    user_data = get_user_data()
    
    # Prepare data for charts
    category_totals = {}
    monthly_totals = {}
    daily_totals = {}
    
    for date, expenses in user_data.items():
        try:
            date_obj = datetime.datetime.strptime(date, "%Y-%m-%d")
            month_key = date_obj.strftime("%Y-%m")
            
            daily_total = 0
            for expense in expenses:
                amount = expense['amount']
                category = expense['category']
                
                # Category totals
                category_totals[category] = category_totals.get(category, 0) + amount
                
                # Daily totals
                daily_total += amount
            
            # Store daily total
            daily_totals[date] = daily_total
            
            # Monthly totals
            monthly_totals[month_key] = monthly_totals.get(month_key, 0) + daily_total
            
        except ValueError:
            continue
    
    # Get recent months (last 6 months)
    recent_months = []
    now = datetime.datetime.now()
    for i in range(6):
        month_date = now.replace(day=1) - datetime.timedelta(days=i*30)
        month_key = month_date.strftime("%Y-%m")
        recent_months.append({
            'month': month_date.strftime("%B %Y"),
            'key': month_key,
            'total': monthly_totals.get(month_key, 0)
        })
    recent_months.reverse()
    
    # Get recent daily expenses (last 30 days)
    recent_days = []
    for i in range(30):
        day_date = now - datetime.timedelta(days=i)
        day_key = day_date.strftime("%Y-%m-%d")
        recent_days.append({
            'date': day_date.strftime("%m/%d"),
            'key': day_key,
            'total': daily_totals.get(day_key, 0)
        })
    recent_days.reverse()
    
    return render_template('analytics.html', 
                         category_totals=category_totals,
                         monthly_totals=recent_months,
                         daily_totals=recent_days,
                         total_expenses=sum(category_totals.values()),
                         total_transactions=sum(len(expenses) for expenses in user_data.values()))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)