from rest_framework.views import exception_handler
from rest_framework.response import Response
import logging

logger = logging.getLogger(__name__)

def custom_exception_handler(exc, context):
    # Let DRF handle standard exceptions (404, ValidationError, etc.)
    response = exception_handler(exc, context)

    if response is not None:
        return response

    # Log all unhandled exceptions (this will go to your server logs)
    logger.exception(f"Unhandled exception in view: {context.get('view')}, Exception: {exc}")

    # Return a generic error response to the client
    return Response(
        {"error": "Internal server error", "details": str(exc)},
        status=500
    )