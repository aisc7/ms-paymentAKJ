import os
import json  
from dotenv import load_dotenv
from flask import Flask, request, jsonify
from flask_pymongo import PyMongo
from datetime import datetime, timedelta
import requests

import logging
from epaycosdk.epayco import Epayco

## Carga las variables de entorno 
load_dotenv()

app = Flask(__name__)

# Configuración de ePayco
epayco = Epayco({
    "apiKey": os.getenv("EPAYCO_PUBLIC_KEY"),  
    "privateKey": os.getenv("EPAYCO_PRIVATE_KEY"),
    "lenguage": "ES",
    "test": os.getenv("EPAYCO_TEST") == 'True'  
})

# Verifica que se haya inicializado correctamente
print("ePayco inicializado correctamente.")

def create_token(data):
    try:
        card_info = { 
            "card[number]": data["card_number"],
            "card[exp_year]": data["exp_year"],
            "card[exp_month]": data["exp_month"],
            "card[cvc]": data["cvc"],
            "hasCvv": True
        }
        token = epayco.token.create(card_info)
        return token 
    except Exception as e:
        return {"error": str(e)}

## Método para crear el cliente 
def create_customer(token, data):
    customer_info = {
        "name": data["name"],
        "last_name": data["last_name"],
        "email": data["email"],
        "phone": data["phone"],
        "default": True
    }
    # Token de la tarjeta
    customer_info["token_card"] = token
    try:
        customer = epayco.customer.create(customer_info)
        return customer
    except Exception as e:
        return {"error": str(e)}

## Método para procesar el pago 
def process_payment(data, customer_id, token_card):
    try:
        # Información para procesar el pago
        payment_info = {
            "token_card": token_card,
            "customer_id": customer_id,
            "doc_type": "CC",
            "doc_number": data["doc_number"],
            "name": data["name"],
            "last_name": data["last_name"],
            "email": data["email"],
            "city": data["city"],
            "address": data["address"],
            "phone": data["phone"],
            "cell_phone": data["cell_phone"],
            "bill": data["bill"],
            "description": "Pago de servicios",
            "value": data["value"],
            "tax": "0",
            "tax_base": data["value"],
            "currency": "COP"
        }
        ## Se crea un pago en ePayco y se devuelve un JSON que indica si el pago se realizó o no 
        response = epayco.charge.create(payment_info)
        return response
    except Exception as e:
        return {"error": str(e)}

## Endpoint para manejar todo el flujo del pago
@app.route("/process-payment", methods=["POST"])
def handle_process_payment():
    data = request.json
    
    # Crea el token de la tarjeta
    token_response = create_token(data)
    print("Token response", json.dumps(token_response))
    
    ## Verifica si hubo un error al crear el token
    if token_response.get("status") is False:
        return jsonify(token_response), 500
    
    ## Extraer id del token
    token_card = token_response["id"] 
    
    ## Crear el cliente 
    customer_response = create_customer(token_card, data)
    print("Customer response", json.dumps(customer_response))
    
    ## Verificar si hubo un error al crear el cliente
    if "error" in customer_response:
        return jsonify(customer_response), 500
    
    ## Extrae el id del cliente 
    customer_id = customer_response["data"]["customerId"]
    
    # Procesar el pago
    payment_response = process_payment(data, customer_id, token_card)
    print("Payment response", json.dumps(payment_response))
    
    ## Verificar si hubo un error al procesar el pago 
    if "error" in payment_response:
        return jsonify(payment_response), 500
    
    return jsonify(payment_response), 200

if __name__ == "__main__":
    app.run(debug=True, port=5002)
