# Mobile app (Flutter)

Android and iOS app for AI Study Coach. Owner: Omar Mustafa (frontend lead). App work starts in Week 2.

## Create the project (once, Week 2 Day 1)

From the repo root, with Flutter stable installed (`flutter --version`):

```bash
cd apps/mobile
flutter create --org com.studycoach --project-name study_coach --platforms android,ios .
flutter pub add flutter_riverpod go_router dio supabase_flutter freezed_annotation json_annotation intl
flutter pub add flutter_localizations --sdk=flutter
flutter pub add --dev build_runner freezed json_serializable very_good_analysis mocktail
```

Keep the `analysis_options.yaml` and `config/` already in this folder; `flutter create` won't overwrite them.

## Folder structure (feature-first)

```
apps/mobile/
├── lib/
│   ├── main.dart                     # reads the flavor config, starts the app
│   ├── app.dart                      # MaterialApp.router, theme, locales, RTL
│   ├── core/
│   │   ├── config/app_config.dart    # API_BASE_URL, SUPABASE_URL, SUPABASE_ANON_KEY from --dart-define
│   │   ├── network/api_client.dart   # the ONLY place that calls our API (dio)
│   │   ├── router/app_router.dart    # go_router routes
│   │   ├── theme/                    # colors, text styles, spacing
│   │   └── widgets/                  # shared widgets used by 2+ features
│   ├── features/
│   │   ├── auth/                     # sign up, log in
│   │   ├── courses/                  # course picker, course spaces, invite links
│   │   ├── lectures/                 # upload, summaries, flashcards
│   │   ├── quizzes/                  # quiz screens, attempts
│   │   ├── study_plan/               # daily plan, re-planning
│   │   └── readiness/                # readiness score per exam
│   │       ├── data/                 # API calls + JSON models (freezed / json_serializable)
│   │       ├── domain/               # plain Dart entities and logic
│   │       └── presentation/         # screens, widgets, Riverpod providers
│   └── l10n/
│       ├── app_ar.arb                # Arabic (default)
│       └── app_en.arb                # English
├── test/                             # mirrors lib/: unit + widget tests
├── integration_test/                 # sign up -> upload -> quiz -> plan
├── config/
│   ├── dev.json.example              # copy to dev.json / staging.json / prod.json (git-ignored)
└── analysis_options.yaml
```

## Run it

```bash
cp config/dev.json.example config/dev.json      # fill in dev values from Amr
flutter run --dart-define-from-file=config/dev.json
flutter analyze && flutter test
```

Full code and deployment rules: root `README.md`, sections 3.7 and 5.
