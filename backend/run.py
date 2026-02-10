from app import create_app

app = create_app()

if __name__ == '__main__':
    print("=" * 60)
    print("  Hospital Management System API")
    print("  Running on http://localhost:5000")
    print("=" * 60)
    app.run(host='0.0.0.0', port=5000, debug=True)
