from flask import Flask, request, render_template_string 
import requests 
 
app = Flask(__name__) 
 
BACKEND_API_URL = "https://venfapp1-caaqbmfdg4djbrce.centralindia-01.azurewebsites.net/api/customers?code=Or1bf1aRM0mw8Kz21hgSFU8I4ny3unkWBNhJbmTMQ3IDAzFuyXjb-A==" 
 
 
FORM_HTML = """ 
<h2>Customer Entry</h2> 
 
<form method="post"> 
    Customer Id<br> 
    <input name="id" type="number"><br><br> 
 
    Name<br> 
    <input name="name"><br><br> 
 
    Salary<br> 
    <input name="salary" type="number" step="0.01"><br><br> 
 
    Address<br> 
    <textarea name="address"></textarea><br><br> 
 
    <button type="submit">Save Customer</button> 
</form> 
 
<p>{{ message }}</p> 
""" 
 
@app.route("/", methods=["GET", "POST"]) 
def customer_form(): 
    message = "" 
    if request.method == "POST": 
        payload = { 
            "id": int(request.form["id"]), 
            "name": request.form["name"], 
            "salary": float(request.form["salary"]), 
            "address": request.form["address"] 
        } 
 
        try: 
            response = requests.post( 
                BACKEND_API_URL, 
                json=payload, 
                timeout=30 
            ) 
 
            message = response.text 
 
        except Exception as e: 
            message = f"Error: {str(e)}" 
 
    return render_template_string(FORM_HTML, message=message) 
 
if __name__ == "__main__": 
    app.run(debug=True, port=5000) 