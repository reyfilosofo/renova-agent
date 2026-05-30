export type RenovaPrinciple = {
  title: string;
  description: string;
};

export type AgentCapability = {
  name: string;
  description: string;
  status: "prototype" | "planned" | "research";
};

export const renovaThesis =
  "La ℛenova is an ontological, existential and renewative framework: a way of measuring, designing and amplifying the conditions under which life, meaning, systems, communities and worlds can be renewed without reducing existence to extraction, automation or mere optimization.";

export const signature = "Rey Filósofo by SERESARTE";

export const principles: RenovaPrinciple[] = [
  {
    title: "Life before optimization",
    description:
      "The system treats life, care, meaning and continuity as first-order variables rather than as collateral effects of efficiency."
  },
  {
    title: "Renewative capacity",
    description:
      "Renewative capacity names the power of a system to generate new viable conditions for life, not merely to restore a previous state."
  },
  {
    title: "Ontological accountability",
    description:
      "Every intervention must ask what kind of world it is making more probable."
  },
  {
    title: "Symbolic precision",
    description:
      "Language, diagrams, equations and interfaces are treated as operational instruments, not decorative surfaces."
  }
];
