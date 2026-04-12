"""
TOPIC: Object-Oriented Programming (OOP) Basics
REFERENCE: https://realpython.com/python3-object-oriented-programming/

KEY TEACHING POINTS:
1. Blueprinting: A 'class' defines what an account IS and DOES.
2. State Management: 'self.balance' keeps track of an individual account's
   money independently of other accounts.
3. Dunder Methods: '__init__' initializes the object, while '__str__'
   customizes how the object appears when printed.
4. Mutation: Methods like 'deposit' and 'withdraw' are the only professional
   way to alter the object's internal data.
"""


class Account:
    def __init__(self, identifier):
        # Initializing instance attributes
        self.identifier = identifier
        self.balance = 0.0

    def __str__(self):
        # Returns a user-friendly string representation
        return f"Account [ID: {self.identifier}] | Balance: ${self.balance:,.2f}"

    def get_balance(self):
        """Helper method to retrieve the current balance."""
        return self.balance

    def deposit(self, amount):
        """Increases the balance by the specified amount."""
        self.balance += amount
        print(f"Deposited ${amount:.2f} to {self.identifier}")

    def withdraw(self, amount):
        """Decreases the balance, assuming sufficient funds."""
        if amount <= self.balance:
            self.balance -= amount
            print(f"Withdrew ${amount:.2f} from {self.identifier}")
        else:
            print("Error: Insufficient funds!")


if __name__ == '__main__':
    # Creating unique instances from the blueprint
    account_1 = Account('ABC-123')
    account_2 = Account('XYZ-789')

    account_1.deposit(100.50)
    account_1.withdraw(20.15)

    # Notice how account_2 remains at $0.00; its state is independent!
    print(account_1)
    print(account_2)

