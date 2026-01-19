from flask import Flask, jsonify, render_template, request, flash, redirect
from flask_sqlalchemy import SQLAlchemy
import pandas as pd
import os

app = Flask(__name__)
app.secret_key = "code123"

# configuration

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///comments.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# database model

class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    comment = db.Column(db.Text, nullable=False)
    comment_type = db.Column(db.String(50), nullable=False)
    severity = db.Column(db.String(20))
    category = db.Column(db.String(50))
    example_fix = db.Column(db.Text)

    def to_dict(self):
        return {
            "id": self.id,
            "comment": self.comment,
            "comment_type": (self.comment_type[:1].upper() + self.comment_type[1:].lower()) if self.comment_type else None, #capitalised
            "severity": (self.severity[:1].upper() + self.severity[1:].lower()) if self.severity else None,
            "category": self.category,
            "example_fix": self.example_fix,
        }

# creates and initialises database

with app.app_context():
    db.create_all()

# all the routes


#LOADS COMMENTS FROM THE CSV FILE INTO THE SQL DATABASE

@app.route("/api/comments/load", methods=["POST"])
def load_comments():
    """Load comments from comments.csv into the database."""
    file_path = os.path.join(os.getcwd(), "comments.csv")

    if not os.path.exists(file_path):
        return jsonify({"error": "comments.csv not found"}), 404

    df = pd.read_csv(file_path)

    # clean up old data before inserting
    Comment.query.delete()

    for _, row in df.iterrows():
        c = Comment(
            comment=row.get("comment"),
            comment_type=row.get("comment-type"),
            severity=row.get("severity"),
            category=row.get("category"),
            example_fix=row.get("example_fix")
        )
        db.session.add(c)

    db.session.commit()
    return jsonify({"message": "CSV data loaded successfully", "rows": len(df)}), 200




#RETURNS ALL THE COMMENTS IN THE DATABASE AS JSON *

@app.route("/api/comments", methods=["GET"])
def get_all_comments():
    """Return all comments in the database."""
    comments = Comment.query.all()
    return jsonify([c.to_dict() for c in comments])




#RETURNS COMMENTS FILTERED BY SPELLING / STRUCTURE / TERMINOLOGY *
#ERROR HANDLING AND CASE SENSITITIVE, WILL RETURN ERROR

@app.route("/api/comments/type/<string:comment_type>", methods=["GET"])
def get_comments_by_type(comment_type):
    """Return comments filtered by type (case-insensitive)."""
    comment_type = comment_type.strip().lower()
    results = Comment.query.filter(
        db.func.lower(Comment.comment_type) == comment_type
    ).all()
    if not results:
        return jsonify({"error": f"No comments found for type '{comment_type}'"}), 404
    return jsonify([c.to_dict() for c in results]), 200



#RENDERS THE MAIN PAGE INDEX.HTML WHICH LOADS COMMENTS DYNAMICALLY USING JS

@app.route("/")
def home():
    return render_template("index.html")



#ROUTE TO SHOW ALL UNIQUE COMMENT TYPES CURRENTLY STORED IN THE DB

@app.route("/api/debug/types")
def debug_types():
    """See distinct comment_type values currently in the DB."""
    types = db.session.query(Comment.comment_type).distinct().all()
    return jsonify(sorted([t[0] for t in types if t[0]]))




#POST - ADDS A NEW COMMENT TO DATABASE *

@app.route("/api/comments", methods=["POST"])  #when someone sends a post request, this will run
def create_comment():
    #Create a new comment
    data = request.get_json(silent=True) or {}  #turns to python dict

    #pulls out each field from JSON, strip to remove spaces,lower it all for consistency
    comment = (data.get("comment") or "").strip()
    comment_type = (data.get("comment_type") or "").strip().lower()
    severity = (data.get("severity") or "medium").strip().lower()
    category = (data.get("category") or "").strip()
    example_fix = (data.get("example_fix") or "").strip()

    #just valiadtion if comment or comment_type isnt sent
    if not comment or not comment_type:
        return jsonify({"error": "Fields 'comment' and 'comment_type' are required."}), 400

    #constrain to three types
    allowed = {"spelling", "structure", "terminology"}
    if comment_type not in allowed:
        return jsonify({"error": f"comment_type must be one of {sorted(allowed)}"}), 400

    #will create a new record in the database
    new_comment = Comment(
        comment=comment,
        comment_type=comment_type,
        severity=severity,
        category=category,
        example_fix=example_fix
    )
    db.session.add(new_comment) #telling SQLAlchemy u r adding new row
    db.session.commit() #commits and saves

    #sends full comment back formatted 
    return jsonify(new_comment.to_dict()), 201
#Allows my front end to add new comments directly
#will test this - CRUD


#PUT - UPDATES AN EXISTING COMMENT BY ID *

@app.route("/api/comments/<int:comment_id>", methods=["PUT"]) #can pass in any commment id
def update_comment(comment_id):
    #Update an existing comment by ID
    data = request.get_json(silent=True) or {} #turns to a python dict

    #retrive the record by id
    comment = Comment.query.get(comment_id)
    if not comment:
        return jsonify({"error": f"Comment with id {comment_id} not found"}), 404 # just some validation and error return

    # Update fields if provided as its a put request 
    if "comment" in data:
        comment.comment = data["comment"].strip() #strip just cleans everything up


    #checks for comment type, all into lower for consist, validation for the 3, error or updates database
    if "comment_type" in data:
        ctype = data["comment_type"].strip().lower()
        allowed = {"spelling", "structure", "terminology"}
        if ctype not in allowed:
            return jsonify({"error": f"comment_type must be one of {sorted(allowed)}"}), 400
        comment.comment_type = ctype


    #same thing for this here - checks and will update it
    if "severity" in data:
        comment.severity = data["severity"].strip().lower()

    #returns the updated record as json alongside a good ststus
    db.session.commit()
    return jsonify(comment.to_dict()), 200
#allows me to update comments



#DELETES A COMMENT FROM THE DATABASE - *

@app.route("/api/comments/<int:comment_id>", methods=["DELETE"])
def delete_comment(comment_id):
    #Delete a comment by its ID.
    comment = Comment.query.get(comment_id)

    if not comment:
        # Return 404 if the ID doesn’t exist
        return jsonify({"error": f"Comment with ID {comment_id} not found."}), 404

    # Remove it from the database
    db.session.delete(comment)
    db.session.commit()

    return jsonify({"message": f"Comment {comment_id} deleted successfully."}), 200


#EDIT PAGE ROUTE - LOADS A PAGE WITH AN EDIT FORM, PRE FILLED WITH COMMENT DATA
#EDIT
@app.route("/comments/<int:id>/edit", methods=["GET"])
def edit_comment(id):
    comment = Comment.query.get_or_404(id)
    return render_template("edit_comment.html", comment=comment)



#UPDATES THE COMMENT WHEN THE USER SUBMITS THE EDIT FORM

@app.route("/comments/<int:id>/edit", methods=["POST"])
def edit_comment_submit(id):
    comment = Comment.query.get_or_404(id)

    new_comment = request.form.get("comment", "").strip()
    new_type = request.form.get("comment_type", "").strip().lower()
    new_severity = request.form.get("severity", "").strip().lower()

    # Validation
    allowed_types = {"spelling", "structure", "terminology"}
    allowed_severity = {"low", "medium", "high"}

    if new_type not in allowed_types:
        return "Invalid type", 400

    if new_severity not in allowed_severity:
        return "Invalid severity", 400

    comment.comment = new_comment
    comment.comment_type = new_type
    comment.severity = new_severity

    db.session.commit()

    flash("Comment updated successfully!", "success")

    return redirect("/")



# RETRIEVE ONE COMMENT BY ID - *

@app.route("/api/comments/<int:comment_id>", methods=["GET"])
def get_comment(comment_id):
    comment = Comment.query.get(comment_id)
    if not comment:
        return jsonify({"error": f"Comment with id {comment_id} not found"}), 404

    return jsonify(comment.to_dict()), 200


# RUN IT

if __name__ == "__main__":
    app.run(debug=True)



