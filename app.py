from flask import Flask, render_template

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'your-secret-key-here'
    
    # Register blueprints directly to avoid circular imports
    from routes.complaints import complaints_bp
    from routes.departments import departments_bp
    from routes.dashboard import dashboard_bp
    from routes.auth import auth_bp
    
    app.register_blueprint(complaints_bp)
    app.register_blueprint(departments_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(auth_bp)
    
    @app.route('/')
    def index():
        return render_template('index.html')
    
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)