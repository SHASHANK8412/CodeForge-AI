import React, { useState, useEffect } from 'react';
import axios from 'axios';

function TodoList() {
  const [tasks, setTasks] = useState([]);
  const token = localStorage.getItem('token');

  useEffect(() => {
    const fetchTasks = async () => {
      try {
        const response = await axios.get('http://localhost:8000/tasks', { headers: { Authorization: `Bearer ${token}` } });
        setTasks(response.data);
      } catch (error) {
        console.error(error);
      }
    };

    fetchTasks();
  }, [token]);

  return (
    <div>
      <h2>Todo List</h2>
      <ul>
        {tasks.map((task) => (
          <li key={task._id}>{task.title}</li>
        ))}
      </ul>
    </div>
  );
}

export default TodoList;