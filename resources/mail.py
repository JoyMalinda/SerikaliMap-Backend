from flask import request, jsonify, make_response
from flask_restful import Resource
from extensions.limiter import limiter
from services.mail_config import send_contact_email, is_spam
import uuid


class Mail(Resource):

    decorators = [limiter.limit("3 per hour")]  # rate limit

    def post(self):
        data = request.get_json() or {}

        email = data.get("email")
        message = data.get("message")
        honeypot = data.get("middleName")  # hidden field

        # Validate
        if not email or not message:
            return {"error": "Email and message are required"}, 400

        # Spam detection
        if is_spam(message, honeypot):
            return {"error": "Spam detected"}, 400

        # Send email (service function)
        try:
            send_contact_email(email, message)
        except Exception as e:
            print("Email error:", e)
            return {"error": "Failed to send email"}, 500

        # Issue client_id cookie if missing
        response = make_response({"success": True, "message": "Email sent"})

        if not request.cookies.get("client_id"):
            response.set_cookie(
                "client_id",
                value=str(uuid.uuid4()),
                max_age=60 * 60 * 24 * 7,  # 7 days
                httponly=True,
                secure=True,
                samesite="Lax"
            )

        return response
