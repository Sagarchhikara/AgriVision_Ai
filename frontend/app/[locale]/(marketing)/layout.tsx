import "@/app/landing.css";

export default function MarketingLayout({ children }: LayoutProps<"/[locale]">) {
  return <div className="landing">{children}</div>;
}
