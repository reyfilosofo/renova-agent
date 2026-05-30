import { capabilities } from "@/data/capabilities";
import { principles, renovaThesis } from "@/lib/renova";

export type AgentRequest = {
  topic: string;
  depth?: "brief" | "standard" | "doctoral";
};

export type AgentResponse = {
  thesis: string;
  selectedPrinciples: string[];
  proposedModules: string[];
  nextAction: string;
};

export function generateRenovaPlan(request: AgentRequest): AgentResponse {
  const depth = request.depth ?? "standard";
  const selectedPrinciples = principles.map((principle) => principle.title);
  const proposedModules = capabilities.map((capability) => capability.name);

  return {
    thesis: `${renovaThesis} Current focus: ${request.topic}. Depth: ${depth}.`,
    selectedPrinciples,
    proposedModules,
    nextAction:
      "Convert the topic into a structured renewative brief with variables, risks, opportunities, deliverables and a publication path."
  };
}
