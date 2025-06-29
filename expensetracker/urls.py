from django.contrib import admin
from django.urls import path
from api.views import (
    ExpenseListCreateView, ExpenseDetailView, IncomeListCreateView, IncomeDetailView,
    UserDetailView, UserListCreateView, ExpenseListCreateViewLlm, LangChainAgentView,
    IncomeListCreateViewLlm, ResetAllTransactionsView
)
from django.http import HttpResponse

# Optional: Simple health check view for Render
def health_check(request):
    return HttpResponse("OK")

urlpatterns = [
    path('', health_check),  # Health check for Render deployment ✅
    path('admin/', admin.site.urls),

    # users
    path('users/', UserListCreateView.as_view(), name='user-list-create'),
    path('users/<str:pk>/', UserDetailView.as_view(), name='user-detail'),

    # llm
    path('expenses/add/', ExpenseListCreateViewLlm.as_view(), name='add-expense'),
    path('income/add/', IncomeListCreateViewLlm.as_view(), name='add-income'),

    # expenses
    path('expenses/', ExpenseListCreateView.as_view(), name='expense-list-create'),
    path('expenses/<str:pk>/', ExpenseDetailView.as_view(), name='expense-detail'),

    # incomes
    path('incomes/', IncomeListCreateView.as_view(), name='income-list-create'),
    path('incomes/<str:pk>/', IncomeDetailView.as_view(), name='income-detail'),

    # reset
    path('reset-transactions/', ResetAllTransactionsView.as_view(), name='reset-transactions'),

    # langchain
    path('ai/agent/', LangChainAgentView.as_view(), name='langchain-agent'),
]
