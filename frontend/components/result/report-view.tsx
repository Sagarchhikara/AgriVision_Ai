"use client";

import {
  CircleHelp,
  FlaskConical,
  Gauge,
  Leaf,
  type LucideIcon,
  Search,
  ShieldCheck,
  Sprout,
  UserRound,
} from "lucide-react";
import type { ReactNode } from "react";

import { ErrorAlert } from "@/components/error-alert";
import { useI18n } from "@/components/i18n-provider";
import { Skeleton } from "@/components/ui/skeleton";
import type { ReportState } from "@/hooks/use-report";
import type { Report } from "@/lib/api";

/**
 * Which report the backend wrote, and so what its fields mean:
 * - uncertain: severity reflects the uncertainty rather than any disease, and
 *   no treatment is for a confirmed problem. Severity and the chemical list are
 *   never shown, even if the model filled them in against its instructions.
 * - healthy: symptoms are early warning signs, and there is nothing to treat.
 * - standard: a diagnosis that is still wrong about 1 time in 4 on field
 *   photos, so treatment is always framed as conditional on confirmation.
 */
export type ReportVariant = "standard" | "uncertain" | "healthy";

function Section({
  icon: Icon,
  title,
  children,
}: {
  icon: LucideIcon;
  title: string;
  children: ReactNode;
}) {
  return (
    <section className="flex flex-col gap-1.5">
      <h3 className="flex items-center gap-2 font-semibold">
        <Icon aria-hidden className="size-5 shrink-0 text-primary" />
        {title}
      </h3>
      {children}
    </section>
  );
}

function Bullets({ items }: { items: string[] }) {
  return (
    <ul className="flex list-disc flex-col gap-1 pl-5 marker:text-primary">
      {items.map((item) => (
        <li key={item}>{item}</li>
      ))}
    </ul>
  );
}

function Treatment({ report, variant }: { report: Report; variant: ReportVariant }) {
  const { t } = useI18n();
  const { organic = [], chemical = [] } = report.treatment;

  if (variant === "uncertain") {
    return (
      <>
        {organic.length > 0 && (
          <Section icon={Leaf} title={t.report.organicUncertain}>
            <Bullets items={organic} />
          </Section>
        )}
        <Section icon={FlaskConical} title={t.report.chemical}>
          <p>{t.report.chemicalUncertain}</p>
        </Section>
      </>
    );
  }

  return (
    <div className="flex flex-col gap-4 rounded-lg border bg-muted/40 p-4">
      <p className="font-semibold">{t.report.ifConfirmed}</p>
      {organic.length > 0 && (
        <Section icon={Leaf} title={t.report.organic}>
          <Bullets items={organic} />
        </Section>
      )}
      <Section icon={FlaskConical} title={t.report.chemical}>
        {chemical.length > 0 && <Bullets items={chemical} />}
        <p className="font-medium">{t.report.chemicalNote}</p>
      </Section>
    </div>
  );
}

function ReportBody({ report, variant }: { report: Report; variant: ReportVariant }) {
  const { t } = useI18n();
  const symptomsTitle = {
    standard: t.report.symptoms,
    uncertain: t.report.symptomsUncertain,
    healthy: t.report.symptomsHealthy,
  }[variant];

  return (
    <div className="flex flex-col gap-5">
      <Section icon={Sprout} title={t.report.summary}>
        <p>{report.summary}</p>
      </Section>

      {variant === "standard" && (
        <Section icon={Gauge} title={t.report.urgency}>
          <p>
            <strong>{t.report.urgencyLevels[report.severity]}.</strong> {report.severity_reason}
          </p>
        </Section>
      )}

      <Section icon={Search} title={symptomsTitle}>
        <Bullets items={report.symptoms_to_check} />
      </Section>

      {variant !== "healthy" && <Treatment report={report} variant={variant} />}

      <Section
        icon={ShieldCheck}
        title={variant === "healthy" ? t.report.preventionHealthy : t.report.prevention}
      >
        <Bullets items={report.prevention} />
      </Section>

      <Section icon={UserRound} title={t.report.consultExpert}>
        <p>{report.when_to_consult_expert}</p>
      </Section>

      <Section icon={CircleHelp} title={t.report.confidenceNote}>
        <p>{report.confidence_note}</p>
      </Section>
    </div>
  );
}

function ReportSkeleton() {
  const { t } = useI18n();
  return (
    <div className="flex flex-col gap-4">
      <p role="status" className="text-muted-foreground">
        {t.report.loading}
      </p>
      <div aria-hidden className="flex flex-col gap-5">
        {[0, 1, 2].map((block) => (
          <div key={block} className="flex flex-col gap-2">
            <Skeleton className="h-5 w-1/2" />
            <Skeleton className="h-4 w-full" />
            <Skeleton className="h-4 w-5/6" />
          </div>
        ))}
      </div>
    </div>
  );
}

export function ReportView({
  state,
  variant,
  onRetry,
}: {
  state: ReportState;
  variant: ReportVariant;
  onRetry: () => void;
}) {
  const { t } = useI18n();
  return (
    <section aria-labelledby="report-heading" className="flex flex-col gap-3">
      <h2 id="report-heading" className="text-lg font-semibold">
        {t.report.heading}
      </h2>
      {state.status === "loading" && <ReportSkeleton />}
      {state.status === "ready" && <ReportBody report={state.report} variant={variant} />}
      {state.status === "error" && (
        <ErrorAlert
          code={state.code}
          // Reports being switched off won't change by trying again.
          onRetry={state.code === "report_disabled" ? undefined : onRetry}
        />
      )}
    </section>
  );
}
