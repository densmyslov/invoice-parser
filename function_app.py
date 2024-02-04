import azure.functions as func
import logging


def main(req: func.HttpRequest) -> func.HttpResponse:
    result = simple_function()
    return func.HttpResponse(str(result), status_code=200)

def simple_function():
    return 5 * 45