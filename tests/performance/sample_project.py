"""
A small FastAPI + SQLAlchemy shop with a real N+1 query in GET /api/orders, used to verify the
Performance Engineer with actual measurements. write_sample(path) writes it as a project folder.
(Kept as a module so pytest never collects the sample's own tests as AIForge tests.)
"""

from pathlib import Path

FILES = {
    'backend/main.py': 'from fastapi import FastAPI, Depends\nfrom sqlalchemy import Column, ForeignKey, Integer, String, create_engine\nfrom sqlalchemy.orm import Session, declarative_base, relationship, sessionmaker\n\nengine = create_engine("sqlite:///./shop.db", connect_args={"check_same_thread": False})\nSessionLocal = sessionmaker(bind=engine, autoflush=False)\nBase = declarative_base()\n\n\nclass Order(Base):\n    __tablename__ = "orders"\n    id = Column(Integer, primary_key=True)\n    customer = Column(String, nullable=False)\n    items = relationship("Item", back_populates="order")\n\n\nclass Item(Base):\n    __tablename__ = "items"\n    id = Column(Integer, primary_key=True)\n    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)\n    name = Column(String, nullable=False)\n    price = Column(Integer, nullable=False)\n    order = relationship("Order", back_populates="items")\n\n\ndef seed(session: Session, orders: int = 300, items_per_order: int = 4) -> None:\n    if session.query(Order).count():\n        return\n    for i in range(orders):\n        order = Order(customer=f"customer-{i}")\n        session.add(order)\n        session.flush()\n        for j in range(items_per_order):\n            session.add(Item(order_id=order.id, name=f"item-{i}-{j}", price=100 + j))\n    session.commit()\n\n\nBase.metadata.create_all(bind=engine)\nwith SessionLocal() as _session:\n    seed(_session)\n\napp = FastAPI()\n\n\ndef get_db():\n    db = SessionLocal()\n    try:\n        yield db\n    finally:\n        db.close()\n\n\n@app.get("/health")\ndef health():\n    return {"status": "ok"}\n\n\n@app.get("/api/orders")\ndef list_orders(db: Session = Depends(get_db)):\n    result = []\n    for order in db.query(Order).order_by(Order.id).all():\n        items = db.query(Item).filter(Item.order_id == order.id).order_by(Item.id).all()\n        result.append({"id": order.id, "customer": order.customer,\n                       "items": [{"name": i.name, "price": i.price} for i in items],\n                       "total": sum(i.price for i in items)})\n    return result\n\n\n@app.get("/api/customers/count")\ndef customer_count(db: Session = Depends(get_db)):\n    return {"count": db.query(Order).count()}\n',
    'requirements.txt': 'fastapi\nsqlalchemy\nhttpx\n',
    'tests/test_orders.py': 'from fastapi.testclient import TestClient\n\nfrom backend.main import app\n\nclient = TestClient(app)\n\n\ndef test_orders_have_items_and_totals():\n    orders = client.get("/api/orders").json()\n    assert len(orders) == 300\n    first = orders[0]\n    assert first["customer"] == "customer-0"\n    assert [i["name"] for i in first["items"]] == ["item-0-0", "item-0-1", "item-0-2", "item-0-3"]\n    assert first["total"] == 100 + 101 + 102 + 103\n\n\ndef test_count():\n    assert client.get("/api/customers/count").json() == {"count": 300}\n',
}


def write_sample(path) -> Path:
    root = Path(path)
    for rel, content in FILES.items():
        target = root / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
    return root
