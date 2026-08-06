"use strict";

const grid = document.querySelector("#projectGrid");

function normalize(value) {
  return String(value || "").replace(/-/g, " ");
}

function textElement(tag, className, value) {
  const element = document.createElement(tag);
  if (className) element.className = className;
  element.textContent = String(value || "");
  return element;
}

function renderProject(project) {
  const article = document.createElement("article");
  article.className = "project-card";

  const meta = document.createElement("div");
  meta.className = "project-meta";
  for (const value of [project.family, project.status, project.priority]) {
    meta.appendChild(textElement("span", "pill", normalize(value)));
  }

  article.append(
    meta,
    textElement("h3", "", project.title),
    textElement("p", "", project.description),
    textElement("p", "project-path", project.path)
  );
  return article;
}

async function loadProjects() {
  if (!grid) return;
  try {
    const response = await fetch("./data/projects.json");
    if (!response.ok) throw new Error("No se pudo cargar data/projects.json");
    const projects = await response.json();
    if (!Array.isArray(projects)) throw new Error("data/projects.json debe contener una lista");
    grid.replaceChildren(...projects.map(renderProject));
  } catch (error) {
    grid.replaceChildren(
      textElement(
        "p",
        "",
        "No se pudo cargar el registro de proyectos. Revisa data/projects.json."
      )
    );
    console.error(error);
  }
}

loadProjects();
