const grid = document.querySelector('#projectGrid');

function normalize(value) {
  return String(value || '').replace(/-/g, ' ');
}

function renderProject(project) {
  const article = document.createElement('article');
  article.className = 'project-card';
  article.innerHTML = `
    <div class="project-meta">
      <span class="pill">${normalize(project.family)}</span>
      <span class="pill">${normalize(project.status)}</span>
      <span class="pill">${normalize(project.priority)}</span>
    </div>
    <h3>${project.title}</h3>
    <p>${project.description}</p>
    <p class="project-path">${project.path}</p>
  `;
  return article;
}

async function loadProjects() {
  if (!grid) return;
  try {
    const response = await fetch('./data/projects.json');
    if (!response.ok) throw new Error('No se pudo cargar data/projects.json');
    const projects = await response.json();
    grid.replaceChildren(...projects.map(renderProject));
  } catch (error) {
    grid.innerHTML = '<p>No se pudo cargar el registro de proyectos. Revisa data/projects.json.</p>';
    console.error(error);
  }
}

loadProjects();
