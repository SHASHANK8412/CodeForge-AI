import React, { useState } from 'react';
import ProjectHeader from '../components/create/ProjectHeader';
import ProjectDescription from '../components/create/ProjectDescription';
import TechnologySelector from '../components/create/TechnologySelector';
import ProjectOptions from '../components/create/ProjectOptions';
import GenerateButton from '../components/create/GenerateButton';
import GenerationError from '../components/create/GenerationError';
import { submitProjectGeneration } from '../services/api';

export default function CreateProject({ setView, onGenerateSuccess }) {
  const [projectName, setProjectName] = useState('FoodDelivery AI');
  const [description, setDescription] = useState(
    'Build a full-stack food delivery application. Users should be able to register and log in, browse restaurants, search for food, add items to a cart, place orders, and track order status. Include an admin dashboard for restaurant and order management.'
  );

  const [stack, setStack] = useState({
    frontend: 'React',
    backend: 'FastAPI',
    database: 'PostgreSQL',
    styling: 'Tailwind CSS'
  });

  const [options, setOptions] = useState({
    authentication: true,
    testing: true,
    documentation: true,
    docker: true,
    readme_generation: true,
    security_review: true,
    local_llm: true,
    model: 'qwen2.5-coder',
    rag: true,
    code_review: true,
    auto_repair: true
  });

  const [submitting, setSubmitting] = useState(false);
  const [errorMessage, setErrorMessage] = useState('');
  const [nameError, setNameError] = useState(false);

  const handleBack = () => {
    if (setView) {
      setView('landing');
    } else {
      window.location.href = '/';
    }
  };

  const handleSubmit = async () => {
    setErrorMessage('');
    setNameError(false);

    if (!projectName || projectName.trim().length === 0) {
      setNameError(true);
      setErrorMessage('Project Name cannot be empty.');
      return;
    }

    if (!description || description.trim().length === 0) {
      setErrorMessage('Please describe what software project you want AIForge to build.');
      return;
    }

    setSubmitting(true);

    const payload = {
      project_name: projectName.trim(),
      description: description.trim(),
      frontend: stack.frontend,
      backend: stack.backend,
      database: stack.database,
      styling: stack.styling,
      authentication: options.authentication,
      testing: options.testing,
      documentation: options.documentation,
      docker: options.docker,
      security_review: options.security_review,
      local_llm: options.local_llm,
      model: options.model,
      rag: options.rag,
      code_review: options.code_review,
      auto_repair: options.auto_repair
    };

    const res = await submitProjectGeneration(payload);
    setSubmitting(false);

    if (res.success) {
      const generationId = res.generation_id || `aiforge-${Date.now()}`;
      if (onGenerateSuccess) {
        onGenerateSuccess(generationId, projectName);
      } else if (setView) {
        setView('project');
      } else {
        window.location.href = `/projects/${generationId}/build`;
      }
    } else {
      setErrorMessage(res.error || 'AIForge could not start the project generation.');
    }
  };

  return (
    <div className="min-h-screen bg-[#090d16] text-slate-100 font-sans selection:bg-cyan-500 selection:text-white">
      <ProjectHeader onBack={handleBack} />

      <main className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-10 space-y-6">
        {/* Main Content Title */}
        <div className="mb-2">
          <h1 className="text-3xl font-black text-white tracking-tight">
            Create a New Project
          </h1>
          <p className="text-sm text-slate-300 mt-1">
            Tell AIForge what you want to build. AIForge will analyze your requirements and create a complete development plan.
          </p>
        </div>

        {/* Error Notification Card */}
        <GenerationError message={errorMessage} onRetry={handleSubmit} />

        {/* Form Sections */}
        <ProjectDescription description={description} setDescription={setDescription} />

        <TechnologySelector stack={stack} setStack={setStack} />

        <ProjectOptions options={options} setOptions={setOptions} />

        <GenerateButton
          projectName={projectName}
          setProjectName={setProjectName}
          submitting={submitting}
          onSubmit={handleSubmit}
          nameError={nameError}
        />
      </main>
    </div>
  );
}
