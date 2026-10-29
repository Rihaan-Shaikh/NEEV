"use client";

import React, { createContext, useContext, useState, useEffect } from "react";

export type Language = "en" | "hi";

interface LanguageContextType {
  language: Language;
  setLanguage: (lang: Language) => void;
  t: (key: string, defaultText?: string) => string;
}

const translations: Record<string, Record<Language, string>> = {
  // Brand & Header
  "brand.title.hi": {
    en: "National Education Evidence and Verification",
    hi: "राष्ट्रीय शिक्षा साक्ष्य एवं सत्यापन"
  },
  "brand.shortName": {
    en: "NEEV",
    hi: "नींव"
  },
  "brand.fullTitle": {
    en: "National Education Evidence and Verification (NEEV)",
    hi: "राष्ट्रीय शिक्षा साक्ष्य एवं सत्यापन (नींव)"
  },
  "brand.motto": {
    en: "Authorized regulatory oversight and enrolment verification portal",
    hi: "अधिकृत विनियामक निगरानी एवं नामांकन सत्यापन पोर्टल"
  },
  "header.academicYear": {
    en: "Academic session: 2024–2025",
    hi: "शैक्षणिक सत्र: 2024–2025"
  },
  "header.demoEnvironment": {
    en: "Demonstration environment",
    hi: "प्रदर्शन डेटा वातावरण"
  },
  "header.authorizedOfficer": {
    en: "Authorized officer",
    hi: "अधिकृत अधिकारी"
  },
  "header.signOut": {
    en: "Sign out",
    hi: "लॉग आउट"
  },

  // Navigation Items
  "nav.overview": {
    en: "Operational overview",
    hi: "संचालन अवलोकन"
  },
  "nav.riskQueue": {
    en: "Risk review queue",
    hi: "जोखिम समीक्षा पंक्ति"
  },
  "nav.cases": {
    en: "Review cases",
    hi: "समीक्षा प्रकरण"
  },
  "nav.reports": {
    en: "Regulatory reports",
    hi: "नियामक रिपोर्ट"
  },
  "nav.verificationReferences": {
    en: "Verification codes",
    hi: "सत्यापन संदर्भ"
  },
  "nav.integrations": {
    en: "External registries",
    hi: "बाहरी रजिस्ट्री स्थिति"
  },
  "nav.institutions": {
    en: "Institutions",
    hi: "संस्थान"
  },
  "nav.programmes": {
    en: "Approved courses & seats",
    hi: "स्वीकृत पाठ्यक्रम एवं सीटें"
  },
  "nav.submissions": {
    en: "Student lists",
    hi: "छात्र नामांकन सूची"
  },
  "nav.enrolments": {
    en: "Enrolled students",
    hi: "छात्र नामांकन"
  },
  "nav.findings": {
    en: "Compliance alerts",
    hi: "अनुपालन अलर्ट"
  },
  "nav.notifications": {
    en: "Notifications",
    hi: "सूचनाएं"
  },
  "nav.activeWorkspace": {
    en: "Active workspace",
    hi: "सक्रिय कार्यक्षेत्र"
  },

  // Common Actions & Buttons
  "action.signIn": {
    en: "Sign in",
    hi: "साइन इन करें"
  },
  "action.submit": {
    en: "Submit",
    hi: "प्रस्तुत करें"
  },
  "action.save": {
    en: "Save changes",
    hi: "परिवर्तन सहेजें"
  },
  "action.cancel": {
    en: "Cancel",
    hi: "रद्द करें"
  },
  "action.close": {
    en: "Close",
    hi: "बंद करें"
  },
  "action.search": {
    en: "Search",
    hi: "खोजें"
  },
  "action.filter": {
    en: "Filter",
    hi: "फ़िल्टर"
  },
  "action.viewDetails": {
    en: "View details",
    hi: "विवरण देखें"
  },
  "action.download": {
    en: "Download",
    hi: "डाउनलोड करें"
  },
  "action.export": {
    en: "Export report",
    hi: "रिपोर्ट निर्यात करें"
  },
  "action.retry": {
    en: "Retry",
    hi: "पुनः प्रयास करें"
  },
  "action.back": {
    en: "Back",
    hi: "वापस जाएं"
  },
  "action.refresh": {
    en: "Refresh",
    hi: "ताज़ा करें"
  },
  "action.clearFilters": {
    en: "Clear filters",
    hi: "फ़िल्टर हटाएं"
  },

  // Common Statuses
  "status.active": {
    en: "Active",
    hi: "सक्रिय"
  },
  "status.pending": {
    en: "Pending",
    hi: "लंबित"
  },
  "status.flagged": {
    en: "Flagged",
    hi: "चिह्नित"
  },
  "status.resolved": {
    en: "Resolved",
    hi: "समाधानित"
  },
  "status.underReview": {
    en: "Under review",
    hi: "समीक्षाधीन"
  },
  "status.dismissed": {
    en: "Dismissed",
    hi: "खारिज"
  },
  "status.escalated": {
    en: "Escalated",
    hi: "उच्चाधिकारी को प्रेषित"
  },
  "status.open": {
    en: "Open",
    hi: "खुला"
  },
  "status.verified": {
    en: "Verified",
    hi: "सत्यापित"
  },

  // Common Labels
  "label.all": {
    en: "All",
    hi: "सभी"
  },
  "label.status": {
    en: "Status",
    hi: "स्थिति"
  },
  "label.date": {
    en: "Date",
    hi: "दिनांक"
  },
  "label.institution": {
    en: "Institution",
    hi: "संस्थान"
  },
  "label.programme": {
    en: "Programme",
    hi: "पाठ्यक्रम"
  },
  "label.academicYear": {
    en: "Academic year",
    hi: "शैक्षणिक वर्ष"
  },
  "label.totalRecords": {
    en: "Total records",
    hi: "कुल रिकॉर्ड"
  },
  "label.page": {
    en: "Page",
    hi: "पृष्ठ"
  },
  "label.actions": {
    en: "Actions",
    hi: "कार्रवाई"
  }
};

const LanguageContext = createContext<LanguageContextType>({
  language: "en",
  setLanguage: () => {},
  t: (key: string, defaultText?: string) => defaultText || key,
});

export function LanguageProvider({ children }: { children: React.ReactNode }) {
  const [language, setLanguageState] = useState<Language>("en");

  useEffect(() => {
    try {
      const stored = localStorage.getItem("neev_portal_language") as Language;
      if (stored === "en" || stored === "hi") {
        setLanguageState(stored);
      }
    } catch {
      // Ignore localStorage exceptions
    }
  }, []);

  const setLanguage = (lang: Language) => {
    setLanguageState(lang);
    try {
      localStorage.setItem("neev_portal_language", lang);
    } catch {
      // Ignore
    }
  };

  const t = (key: string, defaultText?: string): string => {
    const entry = translations[key];
    if (entry && entry[language]) {
      return entry[language];
    }
    return defaultText || key;
  };

  return (
    <LanguageContext.Provider value={{ language, setLanguage, t }}>
      {children}
    </LanguageContext.Provider>
  );
}

export function useLanguage() {
  return useContext(LanguageContext);
}

