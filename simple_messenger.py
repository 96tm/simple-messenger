from app import create_app, database
from config import ProductionConfig


app = create_app(ProductionConfig.name)


@app.shell_context_processor
def make_shell_context():
    return {'database': database}
