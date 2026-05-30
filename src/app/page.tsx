import Image from "next/image";
import { Badge } from "@/components/Badge";
import { CapabilityCard } from "@/components/CapabilityCard";
import { Section } from "@/components/Section";
import { capabilities } from "@/data/capabilities";
import { principles, renovaThesis, signature } from "@/lib/renova";

export default function Home() {
  return (
    <main>
      <section className="hero">
        <div className="heroContent">
          <Badge>Ontological · Existential · ℛenovative</Badge>
          <h1>RENOVA Agent</h1>
          <p className="heroLead">{renovaThesis}</p>
          <div className="heroActions">
            <a href="#architecture">View architecture</a>
            <a href="#capabilities" className="secondaryLink">Explore capabilities</a>
          </div>
        </div>
        <div className="heroVisual" aria-label="RENOVA symbolic diagram">
          <Image src="/assets/hero-renova.svg" width={620} height={620} alt="Abstract diagram of RENOVA Agent" priority />
        </div>
      </section>

      <Section eyebrow="Thesis" title="An AI interface for ℛenovative intelligence">
        <p>
          RENOVA Agent is not only a chatbot wrapper. It is a conceptual operating layer for transforming philosophical, artistic, scientific and institutional material into structured action: diagnosis, writing, diagrams, indices, software artifacts and public communication.
        </p>
      </Section>

      <Section eyebrow="Principles" title="What the system must preserve">
        <div className="grid two">
          {principles.map((principle) => (
            <article className="card" key={principle.title}>
              <h3>{principle.title}</h3>
              <p>{principle.description}</p>
            </article>
          ))}
        </div>
      </Section>

      <Section eyebrow="Capabilities" title="First agent modules" >
        <div id="capabilities" className="grid three">
          {capabilities.map((capability) => (
            <CapabilityCard capability={capability} key={capability.name} />
          ))}
        </div>
      </Section>

      <Section eyebrow="Architecture" title="A modular path from concept to system">
        <div id="architecture" className="architecturePanel">
          <Image src="/assets/architecture.svg" width={980} height={460} alt="RENOVA Agent architecture diagram" />
        </div>
      </Section>

      <Section eyebrow="Next modules" title="Where Codex should take this repository">
        <ol className="roadmapList">
          <li>Interactive prompt console for ℛenovative briefs.</li>
          <li>Document ingestion with source tracking.</li>
          <li>ℛenovative index prototype with variables and weights.</li>
          <li>Editorial generator for essays, books and social posts.</li>
          <li>Deployment pipeline for Vercel and GitHub Actions.</li>
        </ol>
      </Section>

      <footer>
        <Image src="/assets/logo-renova.svg" width={120} height={120} alt="RENOVA Agent logo" />
        <p>{signature}</p>
      </footer>
    </main>
  );
}
