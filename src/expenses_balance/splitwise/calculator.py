from dataclasses import dataclass
from splitwise.expense import Expense
from splitwise.user import ExpenseUser, User, Group
from splitwise import Splitwise
import os

from src.exceptions import AccountingError
from src.models.app_uesr import FamilyMember


class CostILS:
    def __init__(self, cost_agorot: int):
        self._cost = cost_agorot

    @property
    def cost_ils(self):
        return self._cost / 100

    @property
    def cost_agorot(self):
        return self._cost

    def __add__(self, other):
        if isinstance(other, CostILS):
            return CostILS(self._cost + other._cost)
        raise TypeError(f"Unsupported type for addition: {type(other)}")

    def __sub__(self, other):
        if isinstance(other, CostILS):
            return CostILS(self._cost - other._cost)
        raise TypeError(f"Unsupported type for subtraction: {type(other)}")

    def __mul__(self, other):
        if isinstance(other, (int, float)):
            return CostILS(int(self._cost * other))
        raise TypeError(f"Unsupported type for multiplication: {type(other)}")

    def __truediv__(self, other):
        if isinstance(other, (int, float)):
            return CostILS(int(self._cost / other))
        raise TypeError(f"Unsupported type for division: {type(other)}")

    def __floordiv__(self, other):
        if isinstance(other, (int, float)):
            return CostILS(int(self._cost // other))
        raise TypeError(f"Unsupported type for floor division: {type(other)}")

    def __mod__(self, other):
        if isinstance(other, (int, float)):
            return CostILS(int(self._cost % other))
        raise TypeError(f"Unsupported type for modulo: {type(other)}")

    def __lt__(self, other):
        if isinstance(other, CostILS):
            return self._cost < other._cost
        raise TypeError(f"Unsupported type for less than: {type(other)}")

    def __str__(self):
        return f"{self.cost_ils:.2f} ₪"

    def __repr__(self):
        return f"CostILS({self.cost_ils:.2f})"

    @property
    def currency_code(self):
        return "ILS"

    @classmethod
    def from_shekel(cls, total: str | float):
        return cls(int(float(total) * 100))

@dataclass
class DisplayUser:
    username: str
    email: str
    splitwise_user: User

    def __str__(self):
        return f"{self.username} ({self.email})"
@dataclass
class Debt:
    cost: CostILS
    from_split_user: DisplayUser
    to_split_user: DisplayUser


@dataclass
class SplitWiseConfig:
    consumer_key: str
    consumer_secret: str
    api_key: str
    group_id: int

    @classmethod
    def from_env(cls):
        return cls(
            consumer_key=os.environ["SPLITWISE_CONSUMER_KEY"],
            consumer_secret=os.environ["SPLITWISE_CONSUMER_SECRET"],
            api_key=os.environ["SPLITWISE_API_KEY"],
            group_id=int(os.environ["SPLITWISE_GROUP_ID"]),
        )


class SplitCalc:
    def __init__(self, splitwise_config: SplitWiseConfig):
        self.splitwise_config = splitwise_config
        self._splitwise = Splitwise(
            consumer_key=splitwise_config.consumer_key,
            consumer_secret=splitwise_config.consumer_secret,
            api_key=splitwise_config.api_key,
        )
        self._user = self._splitwise.getCurrentUser()
        self._group: Group = self._splitwise.getGroup(splitwise_config.group_id)
        self._users_by_id = {user.id: user for user in self._group.members}

    def user_from_email(self, email_address: str) -> User:
        for user in self._group.members:
            if user.email == email_address:
                return user
        raise ValueError(f"{email_address} was not found in group {self._group.name}")

    def add_equal_split_expense(
        self,
        cost: CostILS,
        description: str,
        paying_user: User
    ):
        """

        Args:
            cost: CostILS object representing the cost in ILS
            description:
            paying_user:

        Returns:

        """
        expense = Expense()
        expense.setGroupId(self._group.id)
        expense.setCost(str(cost.cost_ils))
        expense.setCurrencyCode(cost.currency_code)
        expense.setDescription(description)

        user1 = ExpenseUser()
        user1.setId(paying_user.id)
        user1.setPaidShare(str(cost.cost_ils))

        expense.setSplitEqually()

        expense, errors = self._splitwise.createExpense(expense)
        if errors:
            raise AccountingError(str(errors.errors))
        return expense

    def get_user(self, user_id: int) -> User:
        """
        Get a user by email address.

        Args:
            email: The email address of the user.

        Returns:
            User object representing the user.

        Raises:
            ValueError: If the user is not found in the group.
        """
        try:
            return self._users_by_id[user_id]
        except KeyError:
            pass
        # If not found in the cached dictionary, fetch from Splitwise
        user = self._splitwise.getUser(user_id)
        if not user:
            raise ValueError(f"User with ID {user_id} not found in group {self._group.name}")
        self._users_by_id[user.id] = user
        return user

    def get_balance(self) -> list[Debt]:
        # refresh the group to get the latest balance
        self._group = self._splitwise.getGroup(self.splitwise_config.group_id)
        balance = self._group.getSimplifiedDebts()
        transformed = []
        for debt in balance:
            from_split_user = self.get_user(debt.fromUser)
            to_split_user = self.get_user(debt.toUser)

            transformed.append(
                Debt(
                    cost=CostILS.from_shekel(debt.amount),
                    from_split_user=DisplayUser(
                        username=from_split_user.first_name,
                        email=from_split_user.email,
                        splitwise_user=from_split_user,
                    ),
                    to_split_user=DisplayUser(
                        username=to_split_user.first_name,
                        email=to_split_user.email,
                        splitwise_user=to_split_user,
                    ),

                )
            )

        return transformed


