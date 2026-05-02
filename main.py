from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI()

class TodoCreate(BaseModel):
    title: str
    description: str = ""

todos = []
next_id = 1

@app.get("/")
def root():
    return {"message": "Todo API is running"}

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/todos", status_code=201)
def create_todo(todo: TodoCreate):
    global next_id
    new_todo = {
        "id": next_id,
        "title": todo.title,
        "description": todo.description,
        "completed": False
    }
    todos.append(new_todo)
    next_id += 1
    return new_todo

@app.get("/todos")
def list_todos():
    return todos

@app.get("/todos/{todo_id}")
def get_todo(todo_id: int):
    for todo in todos:
        if todo["id"] == todo_id:
            return todo
    raise HTTPException(status_code=404, detail="Todo not found")

@app.put("/todos/{todo_id}")
def update_todo(todo_id: int, todo_data: TodoCreate):
    for todo in todos:
        if todo["id"] == todo_id:
            todo["title"] = todo_data.title
            todo["description"] = todo_data.description
            return todo
    raise HTTPException(status_code=404, detail="Todo not found")

@app.patch("/todos/{todo_id}/complete")
def complete_todo(todo_id: int):
    for todo in todos:
        if todo["id"] == todo_id:
            todo["completed"] = True
            return todo
    raise HTTPException(status_code=404, detail="Todo not found")

@app.delete("/todos/{todo_id}", status_code=204)
def delete_todo(todo_id: int):
    for i, todo in enumerate(todos):
        if todo["id"] == todo_id:
            todos.pop(i)
            return
    raise HTTPException(status_code=404, detail="Todo not found")
