import React from 'react';
import ProjectCard from './ProjectCard';
import EmptyProjects from './EmptyProjects';

export default function ProjectGrid({
  projects = [],
  onNewProject,
  onOpenProject,
  onOpenCode,
  onOpenQuality,
  onOpenDeploy,
  onRename,
  onDuplicate,
  onArchive,
  onDelete
}) {
  if (!projects || projects.length === 0) {
    return <EmptyProjects onNewProject={onNewProject} />;
  }

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6 font-sans">
      {projects.map((proj) => (
        <ProjectCard
          key={proj.generation_id}
          project={proj}
          onOpenProject={onOpenProject}
          onOpenCode={onOpenCode}
          onOpenQuality={onOpenQuality}
          onOpenDeploy={onOpenDeploy}
          onRename={onRename}
          onDuplicate={onDuplicate}
          onArchive={onArchive}
          onDelete={onDelete}
        />
      ))}
    </div>
  );
}
