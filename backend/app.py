"""
Faculty Allocation System - Flask Backend
"""
from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os

app = Flask(__name__)
CORS(app)
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///allocation.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Models
class Faculty(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), required=True)
    email = db.Column(db.String(100), unique=True, required=True)
    expertise = db.Column(db.String(255))
    max_courses = db.Column(db.Integer, default=3)
    workload = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'expertise': self.expertise,
            'max_courses': self.max_courses,
            'workload': self.workload
        }

class Course(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(20), unique=True, required=True)
    name = db.Column(db.String(100), required=True)
    credits = db.Column(db.Integer, default=3)
    required_expertise = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'code': self.code,
            'name': self.name,
            'credits': self.credits,
            'required_expertise': self.required_expertise
        }

class Allocation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    faculty_id = db.Column(db.Integer, db.ForeignKey('faculty.id'), required=True)
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'), required=True)
    status = db.Column(db.String(20), default='pending')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'faculty_id': self.faculty_id,
            'course_id': self.course_id,
            'status': self.status
        }

# Routes
@app.route('/api/faculty', methods=['GET'])
def get_faculty():
    faculty = Faculty.query.all()
    return jsonify([f.to_dict() for f in faculty])

@app.route('/api/faculty', methods=['POST'])
def create_faculty():
    data = request.json
    faculty = Faculty(
        name=data['name'],
        email=data['email'],
        expertise=data.get('expertise', ''),
        max_courses=data.get('max_courses', 3)
    )
    db.session.add(faculty)
    db.session.commit()
    return jsonify(faculty.to_dict()), 201

@app.route('/api/courses', methods=['GET'])
def get_courses():
    courses = Course.query.all()
    return jsonify([c.to_dict() for c in courses])

@app.route('/api/courses', methods=['POST'])
def create_course():
    data = request.json
    course = Course(
        code=data['code'],
        name=data['name'],
        credits=data.get('credits', 3),
        required_expertise=data.get('required_expertise', '')
    )
    db.session.add(course)
    db.session.commit()
    return jsonify(course.to_dict()), 201

@app.route('/api/allocations/run', methods=['POST'])
def run_allocation():
    """Run allocation algorithm"""
    try:
        faculty = Faculty.query.all()
        courses = Course.query.all()
        
        # Simple greedy allocation
        allocations = []
        course_idx = 0
        
        for f in faculty:
            for _ in range(f.max_courses):
                if course_idx < len(courses):
                    alloc = Allocation(
                        faculty_id=f.id,
                        course_id=courses[course_idx].id,
                        status='allocated'
                    )
                    db.session.add(alloc)
                    allocations.append(alloc.to_dict())
                    course_idx += 1
        
        db.session.commit()
        return jsonify({'status': 'success', 'allocations': allocations})
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'healthy'})

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, host='0.0.0.0', port=5000)
