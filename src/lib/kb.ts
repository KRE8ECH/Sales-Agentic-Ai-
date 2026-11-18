export type HookKind = "news" | "funding" | "role" | "product" | "event" | "social";

export interface KbHook {
  title: string;
  detail: string;
  source: string;
  kind: HookKind;
  publishedAt: string;
}

export interface KbLead {
  slug: string;
  name: string;
  role: string;
  company: string;
  email: string;
  linkedin: string;
  persona: string;
  personaNotes: string;
  snapshot: string;
  roleContext: string;
  hooks: KbHook[];
}

export const OFFER = {
  product: "Cadence",
  positioning:
    "Cadence is the multi-touch outreach system for B2B sales teams that can't afford to sound generic. It researches every lead, drafts a 3–4 touch sequence that references real context, sends on a defined cadence, reads the replies, and only hands a human the leads that are actually worth their time.",
  icp: "Sales leaders at B2B companies with 50–500 employees who run outbound for 5–40 reps.",
  icpShort: "teams like yours",
  outcomes: [
    "lift reply rates by 2–3x versus templated cold email",
    "remove pipeline hygiene work from reps and RevOps",
    "guarantee no lead goes quiet because someone forgot a follow-up",
  ],
  proofPoints: [
    "Teams using Cadence average 34% positive reply rates on first-touch sequences.",
    "A 12-rep manufacturing team recovered 41 stalled opportunities in the first quarter.",
    "Sequences stay consistent across reps, so onboarding a new AE no longer means a ramp of cold-calling roulette.",
  ],
  competitorAngle:
    "Unlike a generic sales-engagement tool, Cadence writes every touch from a live research brief — not from a shared template with a mail-merge field.",
};

export const KB: KbLead[] = [
  {
    slug: "northwind-freight",
    name: "Mara Whitfield",
    role: "VP Revenue Operations",
    company: "Northwind Freight",
    email: "mara.whitfield@northwindfreight.com",
    linkedin: "linkedin.com/in/marawhitfield",
    persona: "operator-turned-vp",
    personaNotes:
      "Built the RevOps stack at a 3PL before this. Cares about reporting hygiene, handoffs between sales and ops, and anything that removes spreadsheet work. Skeptical of tools that add meetings.",
    snapshot:
      "Northwind Freight runs 1,900+ daily less-than-truckload shipments across the US–Mexico corridor, with 340 tractors and 11 terminals. Growth has outpaced the sales org: RevOps was created 8 months ago to unify sales and operations reporting.",
    roleContext:
      "Mara joined 8 months ago from a third-party logistics provider where she built the RevOps function from scratch. She owns CRM hygiene, pipeline reporting, and the outbound motion for the enterprise segment.",
    hooks: [
      {
        title: "Raises $34M Series B to build cross-border Mexico lanes",
        detail:
          "The round is earmarked for lane expansion and a Monterrey consolidation hub, with a stated goal of doubling enterprise revenue in 18 months.",
        source: "Dallas Innovates · 2026-09-14",
        kind: "funding",
        publishedAt: "2026-09-14",
      },
      {
        title: "Opens Monterrey hub, cutting cross-border dwell from 3 days to 9 hours",
        detail:
          "Operations says the hub removes a manual status-update loop that consumed a full-time coordinator per lane.",
        source: "FreightWaves · 2026-10-02",
        kind: "news",
        publishedAt: "2026-10-02",
      },
      {
        title: "Named VP Revenue Operations, first hire in new RevOps org",
        detail:
          "The role was created to unify sales and operations reporting, a mandate that now covers the enterprise outbound motion.",
        source: "LinkedIn · 2026-03-19",
        kind: "role",
        publishedAt: "2026-03-19",
      },
      {
        title: "Posted about replacing a 'frankenstack of spreadsheets' for pipeline reviews",
        detail:
          "Mara wrote that pipeline reviews still take two analysts a day to assemble and that she wants a single source of truth before the Series B growth plan kicks in.",
        source: "LinkedIn post · 2026-10-21",
        kind: "social",
        publishedAt: "2026-10-21",
      },
      {
        title: "Launches shipper portal with live lane pricing for mid-market customers",
        detail:
          "Self-serve pricing is expected to push more inbound volume into a sales org that is still run on spreadsheets.",
        source: "Company blog · 2026-11-03",
        kind: "product",
        publishedAt: "2026-11-03",
      },
    ],
  },
  {
    slug: "helio-health",
    name: "Daniel Okafor",
    role: "Head of Growth",
    company: "Helio Health",
    email: "daniel.okafor@heliohealth.com",
    linkedin: "linkedin.com/in/danielokafor",
    persona: "first-growth-hire",
    personaNotes:
      "First growth hire, ex-athenahealth. Wears multiple hats, allergic to long sales cycles, and measured on pipeline created. Responds to concrete numbers and peer proof.",
    snapshot:
      "Helio Health provides patient intake and scheduling software to regional health systems. 180 employees, 64 health-system customers, roughly $21M ARR. Growth is a mix of inbound and a small enterprise field motion.",
    roleContext:
      "Daniel joined from athenahealth as the first Head of Growth, tasked with building repeatable pipeline beyond the founder-led network. He owns demand gen, SDRs, and the outbound tooling stack.",
    hooks: [
      {
        title: "Lands 12-hospital system contract after a 9-month procurement cycle",
        detail:
          "The win is the largest in company history and came through a referral from an existing customer — a channel Daniel now wants to systematize.",
        source: "Austin Inno · 2026-08-27",
        kind: "news",
        publishedAt: "2026-08-27",
      },
      {
        title: "Launches AI triage screener; pilot cut no-show rate 19%",
        detail:
          "The product story is now clinical outcomes, not just scheduling efficiency — a shift the sales team is still learning to tell.",
        source: "Company blog · 2026-10-11",
        kind: "product",
        publishedAt: "2026-10-11",
      },
      {
        title: "Joins as first Head of Growth from athenahealth",
        detail:
          "Hired to build a repeatable pipeline motion, with a mandate to stand up outbound for the enterprise segment.",
        source: "LinkedIn · 2026-06-02",
        kind: "role",
        publishedAt: "2026-06-02",
      },
      {
        title: "Raises $28M Series B led by Health Velocity",
        detail:
          "Capital is earmarked for the enterprise motion and two new product lines, which means a bigger target account list and more reps to feed.",
        source: "MedCity News · 2026-05-20",
        kind: "funding",
        publishedAt: "2026-05-20",
      },
    ],
  },
  {
    slug: "bluepine-supply",
    name: "Priya Raman",
    role: "Chief Revenue Officer",
    company: "Bluepine Supply",
    email: "priya@bluepinesupply.com",
    linkedin: "linkedin.com/in/priyaraman",
    persona: "enterprise-cro",
    personaNotes:
      "Ex-Coupa, brought in to open the enterprise segment. Cares about forecast accuracy, clean pipeline stages, and repeatable motion over heroics. Values directness.",
    snapshot:
      "Bluepine Supply is a B2B procurement marketplace for industrial MRO, based in Denver with 90 employees. It grew out of a regional distributor network and is now pushing up-market.",
    roleContext:
      "Priya joined from Coupa as the first CRO, tasked with standing up the enterprise motion. She owns the full revenue team and the systems that report on it.",
    hooks: [
      {
        title: "Closes $8M seed led by Foundry Collective",
        detail:
          "The round is explicitly for building an enterprise sales motion, which is Priya's mandate.",
        source: "TechCrunch · 2026-07-15",
        kind: "funding",
        publishedAt: "2026-07-15",
      },
      {
        title: "Crosses $4M GMV in industrial MRO categories",
        detail:
          "Category momentum is strongest in the Mountain West, where two new distribution partnerships just landed.",
        source: "Company blog · 2026-10-30",
        kind: "news",
        publishedAt: "2026-10-30",
      },
      {
        title: "Joins as CRO from Coupa, tasked with first enterprise motion",
        detail:
          "First revenue leadership hire; owns the systems and reporting the board will ask about.",
        source: "LinkedIn · 2026-04-09",
        kind: "role",
        publishedAt: "2026-04-09",
      },
      {
        title: "Partners with two regional distributors in the Mountain West",
        detail:
          "Distribution expansion means more SKUs to sell — and a more complex story to tell enterprise buyers.",
        source: "Press release · 2026-09-22",
        kind: "news",
        publishedAt: "2026-09-22",
      },
    ],
  },
  {
    slug: "quanta-cloud",
    name: "Tomas Lindqvist",
    role: "SVP Sales",
    company: "Quanta Cloud",
    email: "tomas.lindqvist@quantacloud.io",
    linkedin: "linkedin.com/in/tomaslindqvist",
    persona: "enterprise-svp",
    personaNotes:
      "Ex-Datadog, runs global sales. Obsessed with rep productivity and ramp time. Wants systems that scale without adding headcount to RevOps. Direct, metrics-first.",
    snapshot:
      "Quanta Cloud is a DevOps and infrastructure platform, fully remote with 600 employees across 14 countries. Its sales org spans SDRs, AEs, and solutions engineers serving mid-market and enterprise.",
    roleContext:
      "Tomas joined from Datadog to run global sales. He is scaling the AE team fast and is vocal about needing consistent prospecting while new reps ramp.",
    hooks: [
      {
        title: "Hires 40 AEs in Q3 — the largest single-quarter sales expansion to date",
        detail:
          "Ramp consistency is the stated problem: new reps currently get wildly different prospecting support.",
        source: "Company blog · 2026-10-19",
        kind: "news",
        publishedAt: "2026-10-19",
      },
      {
        title: "Achieves SOC 2 Type II as part of an enterprise readiness push",
        detail:
          "Security review was the top blocker in enterprise deals; removing it opens a larger account list.",
        source: "Company blog · 2026-08-08",
        kind: "product",
        publishedAt: "2026-08-08",
      },
      {
        title: "Joins as SVP Sales from Datadog",
        detail:
          "Mandate is to scale the sales org while keeping ramp time under two quarters.",
        source: "LinkedIn · 2026-05-12",
        kind: "role",
        publishedAt: "2026-05-12",
      },
      {
        title: "Launches usage-based pricing tier for platform teams under 50 engineers",
        detail:
          "A new low-friction entry point is expected to feed the funnel with accounts that would never take a sales call.",
        source: "Product release · 2026-11-06",
        kind: "product",
        publishedAt: "2026-11-06",
      },
    ],
  },
  {
    slug: "lumen-retail",
    name: "Alicia Moreno",
    role: "Director of eCommerce",
    company: "Lumen Retail Group",
    email: "alicia.moreno@lumenretail.com",
    linkedin: "linkedin.com/in/aliciomoreno",
    persona: "promoted-operator",
    personaNotes:
      "Promoted internally, now owns site and fulfillment. Stretched thin, reports to the COO. Cares about shipping reliability and digital revenue, not experiments.",
    snapshot:
      "Lumen Retail Group operates 214 stores across the Midwest with a growing digital channel. 1,200 employees, headquartered in Chicago. Digital was reorganized under the COO this year.",
    roleContext:
      "Alicia was promoted to Director of eCommerce this summer — the first role at Lumen that owns both the site and fulfillment. She reports to the COO and is rebuilding her team.",
    hooks: [
      {
        title: "Pilots same-day delivery in 40 stores across Illinois and Indiana",
        detail:
          "The pilot depends on store-level inventory accuracy, which is the team's current bottleneck.",
        source: "Chicago Business Journal · 2026-10-05",
        kind: "news",
        publishedAt: "2026-10-05",
      },
      {
        title: "CIO departs; digital team reorganizes under the COO",
        detail:
          "The reorg put eCommerce under operations, tightening the link between digital promises and store execution.",
        source: "Retail Brew · 2026-09-18",
        kind: "news",
        publishedAt: "2026-09-18",
      },
      {
        title: "Promoted to Director of eCommerce, first to own site and fulfillment",
        detail:
          "Scope doubled overnight; she is now accountable for conversion and on-time delivery together.",
        source: "LinkedIn · 2026-07-07",
        kind: "role",
        publishedAt: "2026-07-07",
      },
      {
        title: "Holiday assortment planning moved two weeks earlier this year",
        detail:
          "The shift signals a more aggressive digital holiday push, with more campaigns to run and coordinate.",
        source: "Company memo · 2026-11-02",
        kind: "news",
        publishedAt: "2026-11-02",
      },
    ],
  },
  {
    slug: "arcline-manufacturing",
    name: "Greg Hahm",
    role: "VP of Sales",
    company: "Arcline Manufacturing",
    email: "greg.hahm@arclinemfg.com",
    linkedin: "linkedin.com/in/greghahm",
    persona: "new-field-leader",
    personaNotes:
      "Ex-Salesforce, first field-sales leadership hire in three years. Inherited a founder-led book. Cares about a real pipeline, not activity theater. Pragmatic, systems-minded.",
    snapshot:
      "Arcline Manufacturing builds industrial IoT sensors and monitoring systems in Cleveland, with 750 employees. It has grown through engineering-led sales and is now professionalizing the field.",
    roleContext:
      "Greg joined from Salesforce as VP of Sales, the first field-sales leadership hire in three years. He owns the newCRM rollout, pipeline hygiene, and a team that has never had a real prospecting motion.",
    hooks: [
      {
        title: "Acquires sensor startup Telemetrix for $61M",
        detail:
          "The deal adds a telemetry line that will be sold through the existing channel — a motion Greg has to build.",
        source: "Cleveland.com · 2026-09-30",
        kind: "news",
        publishedAt: "2026-09-30",
      },
      {
        title: "Joins as VP Sales from Salesforce, first field leadership hire in 3 years",
        detail:
          "Mandate: build a repeatable outbound motion and a pipeline the board can forecast.",
        source: "LinkedIn · 2026-06-15",
        kind: "role",
        publishedAt: "2026-06-15",
      },
      {
        title: "Launches Arcline Insights, a predictive maintenance add-on",
        detail:
          "A new product means a new story for sales to tell and new accounts to open.",
        source: "Press release · 2026-10-14",
        kind: "product",
        publishedAt: "2026-10-14",
      },
      {
        title: "Plant 4 in Ohio adds a second shift, citing demand from EV suppliers",
        detail:
          "Demand is shifting toward EV-adjacent accounts, which are new territory for the sales team.",
        source: "Local news · 2026-11-08",
        kind: "news",
        publishedAt: "2026-11-08",
      },
    ],
  },
  {
    slug: "fable-and-co",
    name: "June Park",
    role: "Founder",
    company: "Fable & Co.",
    email: "june@fableand.co",
    linkedin: "linkedin.com/in/junepark",
    persona: "founder",
    personaNotes:
      "Bootstrapped D2C wellness brand, hands-on. Reads everything, replies fast, hates fluff. Cares about ROAS and repeat purchase. Will only take a call if it's clearly relevant.",
    snapshot:
      "Fable & Co. is a direct-to-consumer wellness brand based in New York with 60 employees. It sells supplements and sleep products online and, as of this fall, in Target nationwide.",
    roleContext:
      "June founded the company and still runs growth personally. She is hiring her first growth hire and building out a creator program.",
    hooks: [
      {
        title: "Expands into Target nationwide with three SKUs",
        detail:
          "Retail distribution changes the growth playbook — more wholesale accounts, fewer pure DTC levers.",
        source: "Modern Retail · 2026-10-09",
        kind: "news",
        publishedAt: "2026-10-09",
      },
      {
        title: "Raises $3.5M seed to grow the creator program",
        detail:
          "Capital is aimed at scaling creator partnerships, which means more partner outreach and coordination.",
        source: "Glossy · 2026-08-19",
        kind: "funding",
        publishedAt: "2026-08-19",
      },
      {
        title: "Launches subscription box; 40% of orders now repeat",
        detail:
          "Retention is becoming the headline metric, shifting focus from acquisition volume to account quality.",
        source: "Company blog · 2026-11-01",
        kind: "product",
        publishedAt: "2026-11-01",
      },
      {
        title: "Posted about hiring a first growth hire instead of a second brand designer",
        detail:
          "June wrote that outbound and partnerships are now the bottleneck, not brand work.",
        source: "LinkedIn · 2026-10-25",
        kind: "social",
        publishedAt: "2026-10-25",
      },
    ],
  },
  {
    slug: "vectra-legal",
    name: "Sarah Chen-Whitmore",
    role: "Chief Revenue Officer",
    company: "Vectra Legal",
    email: "sarah@velegal.com",
    linkedin: "linkedin.com/in/sarahchenwhitmore",
    persona: "scaling-cro",
    personaNotes:
      "Ex-Ironclad, first CRO. Runs a lean team, measured on net revenue retention and pipeline coverage. Analytical; likes seeing the reasoning behind a recommendation.",
    snapshot:
      "Vectra Legal builds contract automation software for mid-market legal teams, based in Boston with 240 employees and about 300 customers.",
    roleContext:
      "Sarah joined from Ironclad as the first CRO. She owns a lean team and is focused on pipeline coverage and a repeatable enterprise motion.",
    hooks: [
      {
        title: "Launches Contract Copilot, an AI assistant for mid-market legal teams",
        detail:
          "A new product line means a new segment to open and a new message the team has to land.",
        source: "Legaltech News · 2026-10-22",
        kind: "product",
        publishedAt: "2026-10-22",
      },
      {
        title: "Joins as first CRO from Ironclad",
        detail:
          "Mandate: build pipeline coverage and a repeatable motion beyond founder-led deals.",
        source: "LinkedIn · 2026-05-28",
        kind: "role",
        publishedAt: "2026-05-28",
      },
      {
        title: "Crosses 300 customers at 94% retention",
        detail:
          "Retention is the sales team's strongest proof point, and it is underused in outbound.",
        source: "Company blog · 2026-09-12",
        kind: "news",
        publishedAt: "2026-09-12",
      },
      {
        title: "Announces integrations with NetSuite and Salesforce",
        detail:
          "Integration coverage removes a common procurement objection and widens the target list.",
        source: "Product update · 2026-11-05",
        kind: "product",
        publishedAt: "2026-11-05",
      },
    ],
  },
];

export function findKbEntry(company: string): KbLead | undefined {
  const norm = company.trim().toLowerCase();
  return KB.find(
    (k) => k.company.toLowerCase() === norm || norm.includes(k.company.toLowerCase())
  );
}
