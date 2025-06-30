from django_ratelimit.decorators import ratelimit
from django_ratelimit.exceptions import Ratelimited
from rest_framework.views import APIView 
from rest_framework.response import Response
from rest_framework import status
from .models import Expense, Income , User
from .serializers import ExpenseSerializer, IncomeSerializer,UserSerializer
from api.langchainAgent.agent import llm,create_user_agent
from datetime import datetime
import logging
from api.langchainAgent.context import set_user_info
from functools import wraps
from django.utils.decorators import method_decorator
import firebase_admin
from django.http import JsonResponse
from firebase_admin import auth, credentials, firestore
import json


import os

# Externalize Firebase credentials path
firebase_json = os.getenv("FIREBASE_CREDENTIALS_JSON")

if not firebase_json:
    raise ValueError("Missing FIREBASE_CREDENTIALS_JSON in environment variables")

# Convert JSON string to dictionary
firebase_cred_dict = json.loads(firebase_json)

# Only initialize once
if not firebase_admin._apps:
    cred = credentials.Certificate(firebase_cred_dict)  # ✅ This works for firebase_admin >= 4.3.0
    # Or: cred = credentials.Certificate.from_json(firebase_cred_dict)  # ✅ safest
    firebase_admin.initialize_app(cred)

# Get Firestore client
db = firestore.client()

def firebase_authenticated(view_func):
    @wraps(view_func)
    def wrapped_view(request, *args, **kwargs):
        auth_header = request.headers.get("Authorization") or request.META.get("HTTP_AUTHORIZATION")

        if not auth_header or not auth_header.startswith("Bearer "):
            return JsonResponse({'error': 'Unauthorized - Missing or Invalid Token'}, status=401)

        try:
            id_token = auth_header.split(" ")[1]
            decoded_token = auth.verify_id_token(id_token)
            request.firebase_user = decoded_token  # ✅ Store in a new field
            request.uid = decoded_token['uid']
        except Exception as e:
            logging.error(f"Invalid Firebase token: {str(e)}")
            return JsonResponse({'error': 'Unauthorized - Token verification failed'}, status=401)

        return view_func(request, *args, **kwargs)

    return wrapped_view


# User Views
@method_decorator(firebase_authenticated, name='dispatch')
class UserListCreateView(APIView):
    # @firebase_authenticated
    def get(self, request):
        print(request.headers)
        users = User.objects.all()
        serializer = UserSerializer(users, many=True)
        return Response(serializer.data)
    # @firebase_authenticated
    @ratelimit(key='ip', rate='10/m', method='POST', block=True)
    def post(self, request):
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@method_decorator(firebase_authenticated, name='dispatch')
class UserDetailView(APIView):
    def get_object(self, pk):
        try:
            return User.objects.get(Id=pk)
        except User.DoesNotExist:
            return None
    def get(self, request, pk):
        user = self.get_object(pk)
        if not user:
            return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)
        serializer = UserSerializer(user)
        return Response(serializer.data)
    def put(self, request, pk):
        user = self.get_object(pk)
        if not user:
            return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)
        serializer = UserSerializer(user, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    def delete(self, request, pk):
        user = self.get_object(pk)
        if not user:
            return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)
        user.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

# Expense Views
@method_decorator(firebase_authenticated, name='dispatch')
class ExpenseListCreateView(APIView):
    def get(self, request):
        expenses = Expense.objects.all()
        serializer = ExpenseSerializer(expenses, many=True)
        return Response(serializer.data)
    def post(self, request):
        serializer = ExpenseSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
@method_decorator(firebase_authenticated, name='dispatch')
class ExpenseDetailView(APIView):

    def get_object(self, pk):
        try:
            return Expense.objects.get(Id=pk)
        except Expense.DoesNotExist:
            return None
       
    def get_objects(self, pk):

        try:
            expenses = Expense.objects.filter(User=pk)
            serializer = ExpenseSerializer(expenses, many=True)
            return serializer.data
        except Expense.DoesNotExist:
            return []            
    def get(self, request, pk):
        expenses = self.get_objects(pk)
        return Response(expenses)
    def put(self, request, pk):
        expense = self.get_object(pk)
        if not expense:
            return Response({"error": "Expense not found"}, status=status.HTTP_404_NOT_FOUND)
        serializer = ExpenseSerializer(expense, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    def delete(self, request, pk):
        expense = self.get_object(pk)
        if not expense:
            return Response({"error": "Expense not found"}, status=status.HTTP_404_NOT_FOUND)
        expense.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


# Income Views
@method_decorator(firebase_authenticated, name='dispatch')
class IncomeListCreateView(APIView):
    def get(self, request):
        incomes = Income.objects.all()
        serializer = IncomeSerializer(incomes, many=True)
        return Response(serializer.data)
    def post(self, request):
        print("Received data:", request.data) 
        serializer = IncomeSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
@method_decorator(firebase_authenticated, name='dispatch')
class IncomeDetailView(APIView):
    def get_object(self, pk):
        try:
            return Income.objects.get(Id=pk)
        except Income.DoesNotExist:
            return None
    def get_objects(self, pk):
        try:
            incomes = Income.objects.filter(User=pk)
            serializer = IncomeSerializer(incomes, many=True)
            return serializer.data
        except Income.DoesNotExist:
            return []   
    def get(self, request, pk):
        incomes = self.get_objects(pk)
        return Response(incomes)
    def put(self, request, pk):
        income = self.get_object(pk)
        if not income:
            return Response({"error": "Income not found"}, status=status.HTTP_404_NOT_FOUND)
        serializer = IncomeSerializer(income, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    def delete(self, request, pk):
        income = self.get_object(pk)
        if not income:
            return Response({"error": "income not found"}, status=status.HTTP_404_NOT_FOUND)
        income.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


@method_decorator(firebase_authenticated, name='dispatch')
class ResetAllTransactionsView(APIView):
    def delete(self, request):
        user = request.uid
        Income.objects.filter(User=user).delete()
        Expense.objects.filter(User=user).delete()
        return Response({"message": "All income and expenses deleted successfully."}, status=status.HTTP_200_OK)

## llm part 
logger = logging.getLogger(__name__)

@method_decorator(firebase_authenticated, name='dispatch')
class LangChainAgentView(APIView):
    @method_decorator(ratelimit(key='ip', rate='5/m', method='POST', block=True))
    def post(self, request):
        user_input = request.data.get("query")
        user_id = request.uid
        id_token = request.headers.get("Authorization")

        if not id_token or not user_id or not user_input:
            return Response({"error": "Missing query, user_id, or token"}, status=status.HTTP_400_BAD_REQUEST)

        auth_token = id_token.split(" ")[1]
        set_user_info(user_id, auth_token)

        chat_history = request.data.get("chat_history") or []
        if not isinstance(chat_history, list):
            chat_history = []

        def is_natural_chat(text: str) -> bool:
            casual_phrases = [
                "hi", "hello", "thanks", "thank you", "how are you", "ok", "okay", "cool",
                "nice", "great", "hmm", "yo", "sup", "good morning", "good evening", "heyy"
            ]
            text = text.strip().lower()
            return any(text.startswith(phrase) or text == phrase for phrase in casual_phrases)

        try:
            logger.info("LangChainAgentView: Invoking agent for user_id: %s with query: '%s'", user_id, user_input)

            if is_natural_chat(user_input):
                logger.info("LangChainAgentView: Detected casual input. Letting base LLM respond.")
                casual_response = llm.invoke(user_input).content
                return Response({"response": casual_response}, status=200)

            # ✅ Create per-user agent with memory
            agent = create_user_agent(user_id)
            config = {"configurable": {"thread_id": user_id}}

            # ✅ Run agent
            response_from_agent = agent.invoke(
                {"messages": [{"role": "user", "content": user_input}]},
                config=config
            )
            final_ai_message = response_from_agent.get("messages", [])[-1]
            logger.info("LangChainAgentView: Agent responded: %s", final_ai_message)

            return Response({"response": final_ai_message.content})

        except Ratelimited:
            logger.warning(f"LangChainAgentView: Rate limit exceeded for IP: {request.META.get('REMOTE_ADDR')}")
            return Response(
                {"error": "Rate limit exceeded. Please wait a minute before making more requests."},
                status=429
            )
        except Exception as e:
            if "quota" in str(e).lower() or "resource exhausted" in str(e).lower():
                logger.error(f"LangChainAgentView: Gemini quota exceeded: {e}")
                return Response({"error": "Our AI service has reached its usage limit for now. Please try again later."}, status=503)
            logger.exception("LangChainAgentView: Agent crashed for input: '%s'", user_input)
            return Response({"error": f"Agent error: {str(e)}"}, status=500)


@method_decorator(firebase_authenticated, name='dispatch')
class ExpenseListCreateViewLlm(APIView):
    # This endpoint is primarily for the LangChain agent to call.
 

    def post(self, request):
        logger.info("ExpenseListCreateViewLlm: POST request received. Remote IP: %s", request.META.get('REMOTE_ADDR'))
        data = request.data

        # Server-side validation for required fields (redundant with tool, but crucial for security)
        required_fields = ["Id", "User", "Title", "Amount", "Tag", "Type", "Date"]
        missing_fields = [field for field in required_fields if field not in data]
        if missing_fields:
            logger.warning("ExpenseListCreateViewLlm: Missing fields in request: %s. Data: %s", ', '.join(missing_fields), data)
            return Response({"error": f"Missing fields: {', '.join(missing_fields)}"}, status=status.HTTP_400_BAD_REQUEST)
        
        # Additional server-side validation for data types/formats
        try:
            # Ensure Amount is a float and positive
            data['Amount'] = float(data['Amount'])
            if data['Amount'] <= 0:
                logger.warning("ExpenseListCreateViewLlm: Invalid amount (must be positive): %s. Data: %s", data['Amount'], data)
                return Response({"error": "Amount must be a positive number."}, status=status.HTTP_400_BAD_REQUEST)

            # Ensure Date is valid and not in the future
            expense_date_obj = datetime.strptime(data['Date'], "%Y-%m-%d").date()
            if expense_date_obj > datetime.now().date():
                logger.warning("ExpenseListCreateViewLlm: Expense date in future: %s. Data: %s", data['Date'], data)
                return Response({"error": "Expense date cannot be in the future."}, status=status.HTTP_400_BAD_REQUEST)
            
            # Reformat date to ensure consistency if needed by serializer/model
            data['Date'] = expense_date_obj.strftime("%Y-%m-%d")

        except (ValueError, TypeError) as ve:
            logger.warning("ExpenseListCreateViewLlm: Data type or format error: %s. Data: %s", str(ve), data)
            return Response({"error": f"Invalid data format: {ve}"}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.exception("ExpenseListCreateViewLlm: Unexpected data processing error for data: %s", data)
            return Response({"error": f"An unexpected data processing error occurred: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        serializer = ExpenseSerializer(data=data)
        if serializer.is_valid():
            try:

                serializer.save()
                logger.info("ExpenseListCreateViewLlm: Expense added successfully. ID: %s by User: %s", data.get("Id"), data.get("User"))
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            except Exception as e:
                logger.exception("ExpenseListCreateViewLlm: Error saving expense through serializer for data: %s", data)
                return Response({"error": f"Failed to save expense: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        else:
            logger.warning("ExpenseListCreateViewLlm: Serializer validation failed: %s. Data: %s", serializer.errors, data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)




@method_decorator(firebase_authenticated, name='dispatch')
class IncomeListCreateViewLlm(APIView):
    # This endpoint is primarily for the LangChain agent/tool to call to add income.

    def post(self, request):
        logger.info("IncomeListCreateViewLlm: POST request received. Remote IP: %s", request.META.get('REMOTE_ADDR'))
        data = request.data

        # Note: 'Type' should explicitly be "Income" for this endpoint's purpose
        required_fields = ["Id", "User", "Title", "Amount", "Tag", "Type", "Date"]
        missing_fields = [field for field in required_fields if field not in data]
        if missing_fields:
            logger.warning("IncomeListCreateViewLlm: Missing fields in request: %s. Data: %s", ', '.join(missing_fields), data)
            return Response({"error": f"Missing fields: {', '.join(missing_fields)}"}, status=status.HTTP_400_BAD_REQUEST)
        
        # Additional server-side validation for data types/formats
        try:
            # Ensure Amount is a float and positive
            data['Amount'] = float(data['Amount'])
            if data['Amount'] <= 0:
                logger.warning("IncomeListCreateViewLlm: Invalid amount (must be positive): %s. Data: %s", data['Amount'], data)
                return Response({"error": "Amount must be a positive number."}, status=status.HTTP_400_BAD_REQUEST)

            # Ensure Date is valid and not in the future (using current date/time)
            income_date_obj = datetime.strptime(data['Date'], "%Y-%m-%d").date()
            if income_date_obj > datetime.now().date(): # Compare only dates, ignoring time
                logger.warning("IncomeListCreateViewLlm: Income date in future: %s. Data: %s", data['Date'], data)
                return Response({"error": "Income date cannot be in the future."}, status=status.HTTP_400_BAD_REQUEST)
            
            # Reformat date to ensure consistency if needed by serializer/model
            data['Date'] = income_date_obj.strftime("%Y-%m-%d")

            # Validate that 'Type' is indeed "Income" for this endpoint
            if data.get('Type') != "Income":
                logger.warning("IncomeListCreateViewLlm: Invalid 'Type' specified. Expected 'Income', got '%s'. Data: %s", data.get('Type'), data)
                return Response({"error": "Invalid 'Type'. This endpoint only accepts 'Income' type."}, status=status.HTTP_400_BAD_REQUEST)

        except (ValueError, TypeError) as ve:
            logger.warning("IncomeListCreateViewLlm: Data type or format error: %s. Data: %s", str(ve), data)
            return Response({"error": f"Invalid data format: {ve}"}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.exception("IncomeListCreateViewLlm: Unexpected data processing error for data: %s", data)
            return Response({"error": f"An unexpected data processing error occurred: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


        serializer = IncomeSerializer(data=data) 
        if serializer.is_valid():
            try:
                serializer.save()
                logger.info("IncomeListCreateViewLlm: Income added successfully. ID: %s by User: %s", data.get("Id"), data.get("User"))
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            except Exception as e:
                logger.exception("IncomeListCreateViewLlm: Error saving income through serializer for data: %s", data)
                return Response({"error": f"Failed to save income: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        else:
            logger.warning("IncomeListCreateViewLlm: Serializer validation failed: %s. Data: %s", serializer.errors, data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

