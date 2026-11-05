import { NextResponse, type NextRequest } from "next/server";

import { isLocale, LOCALE_COOKIE, matchAcceptLanguage } from "@/lib/i18n/config";

/**
 * Sends any path without a locale to the right one: the language the user
 * chose before (cookie), otherwise the browser's preference.
 */
export function proxy(request: NextRequest) {
  const { pathname } = request.nextUrl;
  if (isLocale(pathname.split("/")[1])) return;

  const saved = request.cookies.get(LOCALE_COOKIE)?.value;
  const locale = isLocale(saved)
    ? saved
    : matchAcceptLanguage(request.headers.get("accept-language"));

  const url = request.nextUrl.clone();
  url.pathname = `/${locale}${pathname === "/" ? "" : pathname}`;
  return NextResponse.redirect(url);
}

export const config = {
  matcher: ["/((?!_next|icon.svg|favicon.ico).*)"],
};
