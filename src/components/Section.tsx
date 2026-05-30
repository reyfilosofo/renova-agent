type SectionProps = {
  eyebrow?: string;
  title: string;
  children: React.ReactNode;
};

export function Section({ eyebrow, title, children }: SectionProps) {
  return (
    <section className="section">
      {eyebrow ? <p className="eyebrow">{eyebrow}</p> : null}
      <h2>{title}</h2>
      <div className="sectionBody">{children}</div>
    </section>
  );
}
