"use client";

import {
  CircleHelp,
  FlaskConical,
  Gauge,
  Leaf,
  type LucideIcon,
  Search,
  ShieldCheck,
  UserRound,
  UserRoundCheck,
} from "lucide-react";
import type { ReactNode } from "react";

import { ErrorAlert } from "@/components/error-alert";
import { useI18n } from "@/components/i18n-provider";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { Card } from "@/components/ui/card";
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
  level: Heading = "h3",
  children,
}: {
  icon: LucideIcon;
  title: string;
  level?: "h3" | "h4";
  children: ReactNode;
}) {
  return (
    <section className="grid break-inside-avoid grid-cols-[auto_minmax(0,1fr)] content-start items-center gap-x-3 gap-y-2">
      <span className="grid size-9 place-items-center rounded-lg bg-secondary text-primary">
        <Icon aria-hidden className="size-5" />
      </span>
      <Heading className={Heading === "h3" ? "text-h3" : "font-heading font-semibold"}>
        {title}
      </Heading>
      <div className="col-span-2 flex flex-col gap-2 leading-relaxed md:col-span-1 md:col-start-2">
        {children}
      </div>
    </section>
  );
}

function Row({ children }: { children: ReactNode }) {
  return <div className="p-4 md:p-6 print:px-0">{children}</div>;
}

function Bullets({ items }: { items: string[] }) {
  return (
    <ul className="flex list-disc flex-col gap-2 pl-5 marker:text-selected">
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
      <Row>
        <div className="flex flex-col gap-6">
          {organic.length > 0 && (
            <Section icon={Leaf} title={t.report.organicUncertain}>
              <Bullets items={organic} />
            </Section>
          )}
          <Alert role="note" variant="warning">
            <FlaskConical aria-hidden />
            <AlertTitle>{t.report.chemical}</AlertTitle>
            <AlertDescription>{t.report.chemicalUncertain}</AlertDescription>
          </Alert>
        </div>
      </Row>
    );
  }

  return (
    <Row>
      <div className="overflow-hidden rounded-xl border">
        <div className="flex items-center gap-2.5 bg-secondary px-4 py-3 text-secondary-foreground">
          <UserRoundCheck aria-hidden className="size-5 shrink-0" />
          <h3 className="text-h3">{t.report.ifConfirmed}</h3>
        </div>
        <div className="flex flex-col gap-6 bg-muted/40 p-4">
          {organic.length > 0 && (
            <Section icon={Leaf} title={t.report.organic} level="h4">
              <Bullets items={organic} />
            </Section>
          )}
          <Section icon={FlaskConical} title={t.report.chemical} level="h4">
            {chemical.length > 0 && <Bullets items={chemical} />}
            <p className="border-l-3 border-selected pl-3 font-medium">{t.report.chemicalNote}</p>
          </Section>
        </div>
      </div>
    </Row>
  );
}

const URGENCY_BADGE = { low: "info", medium: "uncertain", high: "error" } as const;

function ReportBody({ report, variant }: { report: Report; variant: ReportVariant }) {
  const { t } = useI18n();
  const symptomsTitle = {
    standard: t.report.symptoms,
    uncertain: t.report.symptomsUncertain,
    healthy: t.report.symptomsHealthy,
  }[variant];

  return (
    <div className="divide-y">
      {report.summary && (
        <div className="break-inside-avoid bg-secondary/40 p-4 md:p-6 print:px-0">
          <h3 className="text-h3 text-secondary-foreground">{t.report.summary}</h3>
          <p className="mt-2 text-lg leading-relaxed">{report.summary}</p>
        </div>
      )}

      {variant === "standard" && (
        <Row>
          <Section icon={Gauge} title={t.report.urgency}>
            <div>
              <Badge variant={URGENCY_BADGE[report.severity]}>
                {t.report.urgencyLevels[report.severity]}
              </Badge>
            </div>
            <p>{report.severity_reason}</p>
          </Section>
        </Row>
      )}

      {report.symptoms_to_check.length > 0 && (
        <Row>
          <Section icon={Search} title={symptomsTitle}>
            <Bullets items={report.symptoms_to_check} />
          </Section>
        </Row>
      )}

      {variant !== "healthy" && <Treatment report={report} variant={variant} />}

      {report.prevention.length > 0 && (
        <Row>
          <Section
            icon={ShieldCheck}
            title={variant === "healthy" ? t.report.preventionHealthy : t.report.prevention}
          >
            <Bullets items={report.prevention} />
          </Section>
        </Row>
      )}

      {(report.when_to_consult_expert || report.confidence_note) && (
        <Row>
          <div className="grid gap-6 @xl:grid-cols-2">
            {report.when_to_consult_expert && (
              <Section icon={UserRound} title={t.report.consultExpert}>
                <p>{report.when_to_consult_expert}</p>
              </Section>
            )}
            {report.confidence_note && (
              <Section icon={CircleHelp} title={t.report.confidenceNote}>
                <p>{report.confidence_note}</p>
              </Section>
            )}
          </div>
        </Row>
      )}
    </div>
  );
}

function ReportSkeleton() {
  const { t } = useI18n();
  return (
    <div className="flex flex-col gap-4">
      <p className="text-muted-foreground">{t.report.loading}</p>
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
  context,
  onRetry,
}: {
  state: ReportState;
  variant: ReportVariant;
  context: string;
  onRetry: () => void;
}) {
  const { t } = useI18n();
  return (
    <section aria-labelledby="report-heading" className="flex flex-col gap-3">
      {/* Always mounted, or the arrival of the report would go unannounced. */}
      <div role="status" className="sr-only">
        {state.status === "loading" && t.report.loading}
        {state.status === "ready" && t.report.ready}
      </div>
      <div className="break-after-avoid">
        <h2 id="report-heading" className="text-h2">
          {t.report.heading}
        </h2>
        <p className="text-sm text-muted-foreground">{context}</p>
      </div>
      {state.status === "loading" && (
        <Card className="p-4 md:p-6">
          <ReportSkeleton />
        </Card>
      )}
      {state.status === "ready" && (
        <Card className="@container overflow-hidden print:border-0 print:shadow-none">
          <ReportBody report={state.report} variant={variant} />
        </Card>
      )}
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
