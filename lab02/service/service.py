import os

from flask import Flask, jsonify, request, abort, send_file

app = Flask(__name__)

app.config['UPLOAD_FOLDER'] = 'new_images'

products = {}
next_id = 1


def get_next_id():
    global next_id
    cur_id = next_id
    next_id += 1
    return cur_id


@app.route("/products", methods=["GET"])
def get_all_products():
    return jsonify(list(products.values())), 200


@app.route("/product/<int:product_id>", methods=["GET"])
def get_product(product_id):
    product = products.get(product_id)
    if product is None:
        abort(404, description=f"Product with id={product_id} not found")
    return jsonify(product), 200


@app.route("/product/<int:product_id>/image", methods=["GET"])
def get_product_icon(product_id):
    product = products.get(product_id)
    if product is None:
        abort(404, description=f"Product with id={product_id} not found")
    if product["icon"] is None:
        abort(404, description=f"Product with id={product_id} has no icon")

    return send_file(product['icon']), 200
    

@app.route("/product", methods=["POST"])
def create_product():
    data = request.get_json()
    if not data:
        abort(400, description="Request body must be JSON")
    name = data.get("name")
    description = data.get("description")
    if not name:
        abort(400, description="Field 'name' is required")
    if not description:
        abort(400, description="Field 'description' is required")
    product_id = get_next_id()
    product = {
        "id" : product_id,
        "name": name, 
        "description"  : description
    }
    products[product_id] = product
    return jsonify(product), 200

@app.route("/product/<int:product_id>/image", methods=["POST"])
def create_product_image(product_id):
    product = products.get(product_id)
    if product is None:
        abort(404, description=f"Product with id={product_id} not found")
    if "icon" not in request.files:
        abort(400, description="Field 'icon' is required")
    icon = request.files["icon"]
    if not icon:
        abort(400, description="Field 'icon' is required")
    if icon.filename == "":
        abort(400, description="Icon file must have a filename")

    path = os.path.join(app.config['UPLOAD_FOLDER'], icon.filename)
    icon.save(path)
    product['icon'] = path
    return jsonify(product), 200


@app.route("/product/<int:product_id>", methods=["PUT"])
def update_product(product_id):
    product = products.get(product_id)
    if product is None:
        abort(404, description=f"Product with id={product_id} not found")
    data = request.get_json()
    if not data:
        abort(400, description="Request body must be JSON")
    name = data.get("name")
    description = data.get("description")
    if name:
        product["name"] = name
    if description:
        product["description"] = description
    return jsonify(product), 200


@app.route("/product/<int:product_id>", methods=["DELETE"])
def delete_product(product_id):
    product = products.get(product_id)
    if product is None:
        abort(404, description=f"Product with id={product_id} not found")
    del products[product_id]
    return jsonify(product), 200


if __name__ == "__main__":
    app.run(debug=True, port=5000)