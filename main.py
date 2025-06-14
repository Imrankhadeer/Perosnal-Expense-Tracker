from database import get_connection, init_db
class Expense:
    def __init__(self, member, value, category, description, date):
        self.member, self.value, self.category, self.description, self.date = \
            member, value, category, description, date

class FamilyExpenseTracker:
    def __init__(self, user_id):
        self.user_id = user_id; init_db()
        self.members, self.expense_list = self.load_members(), self.load_expenses()

    def load_members(self):
        conn = get_connection(); c = conn.cursor()
        c.execute("SELECT name, earning, earnings FROM members WHERE user_id=?", (self.user_id,))
        members = [{"name": r[0], "earning": bool(r[1]), "earnings": r[2]} for r in c.fetchall()]
        conn.close(); return members

    def add_member(self, name, earning=False, earnings=0):
        conn = get_connection()
        conn.execute("INSERT INTO members (user_id, name, earning, earnings) VALUES (?,?,?,?)",
                     (self.user_id, name, earning, earnings))
        conn.commit(); conn.close()
        self.members.append({"name": name, "earning": earning, "earnings": earnings})

    def update_member(self, name, earning, earnings):
        conn = get_connection()
        conn.execute("UPDATE members SET earning=?, earnings=? WHERE user_id=? AND name=?",
                     (earning, earnings, self.user_id, name))
        conn.commit(); conn.close()

    def delete_member(self, name):
        conn = get_connection()
        conn.execute("DELETE FROM members WHERE user_id=? AND name=?", (self.user_id, name))
        conn.commit(); conn.close()
        self.members = [m for m in self.members if m["name"] != name]

    def load_expenses(self):
        conn = get_connection(); c = conn.cursor()
        c.execute("SELECT member, value, category, description, date FROM expenses WHERE user_id=?",
                  (self.user_id,))
        expenses = [Expense(*r) for r in c.fetchall()]
        conn.close(); return expenses

    def add_expense(self, member, value, category, description, date):
        conn = get_connection()
        conn.execute("INSERT INTO expenses (user_id, member, value, category, description, date) VALUES (?,?,?,?,?,?)",
                     (self.user_id, member, value, category, description, date))
        conn.commit(); conn.close()
        self.expense_list.append(Expense(member, value, category, description, date))

    def delete_expense(self, index):
        if 0 <= index < len(self.expense_list):
            e = self.expense_list[index]
            conn = get_connection()
            conn.execute("""DELETE FROM expenses
                            WHERE user_id=? AND member=? AND value=? AND category=?
                              AND description=? AND date=?""",
                         (self.user_id, e.member, e.value, e.category, e.description, e.date))
            conn.commit(); conn.close()
            self.expense_list.pop(index)

    def calculate_total_earnings(self):
        return sum(m["earnings"] for m in self.members if m["earning"])

    def calculate_total_expenditure(self):
        return sum(e.value for e in self.expense_list)

    def get_monthly_summary(self):
        conn = get_connection(); c = conn.cursor()
        c.execute("""
            SELECT SUBSTR(date,1,7) AS month, SUM(value)
            FROM expenses WHERE user_id=?
            GROUP BY month ORDER BY month
        """, (self.user_id,))
        rows = c.fetchall(); conn.close()
        return rows
