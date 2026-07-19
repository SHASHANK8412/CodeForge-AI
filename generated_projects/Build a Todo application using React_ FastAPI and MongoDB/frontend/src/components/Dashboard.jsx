import React, { useState, useEffect } from 'react';
import axios from 'axios';

const Dashboard = () => {
  const [tasks, setTasks] = useState([]);

  useEffect(() => {
    const fetchTasks = async () => {
      try {
        const response = await axios.get('http://localhost:8000/api/tasks/list', {
          headers: { Authorization: `Bearer ${localStorage.getItem('token')}` }
        });
        setTasks(response.data);
      } catch (error) {
        console.error(error.response.data);
      }
    };

    fetchTasks();
  }, []);

  return (
    <div>
      <h1>Dashboard</h1>
      <ul>
        {tasks.map((task) => (
          <li key={task._id}>{task.title}</li>
        ))}
      </ul>
    </div>
  );
};

export default Dashboard;