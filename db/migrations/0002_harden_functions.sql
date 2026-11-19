-- 0002_harden_functions.sql — fixes Supabase security advisor warnings on 0001 (issue #36).
-- SECURITY DEFINER functions in `public` are callable through /rest/v1/rpc. The sign-up
-- trigger function needs no direct callers, and the membership check moves to a schema
-- the REST API does not expose.

begin;

revoke execute on function public.handle_new_user() from public, anon, authenticated;

create schema if not exists private;
revoke all on schema private from public;
grant usage on schema private to authenticated;

create function private.is_course_member(target_course_id integer) returns boolean
language sql stable security definer set search_path = '' as $$
    select exists (
        select 1 from public.course_members m
        where m.course_id = target_course_id and m.user_id = (select auth.uid())
    );
$$;
revoke execute on function private.is_course_member(integer) from public, anon;
grant execute on function private.is_course_member(integer) to authenticated;

alter policy topics_read_members on public.course_topics
    using (private.is_course_member(course_id));
alter policy lectures_read_members on public.lectures
    using (private.is_course_member(course_id));
alter policy chunks_read_members on public.lecture_chunks
    using (private.is_course_member(course_id));
alter policy questions_read_members on public.quiz_questions
    using (private.is_course_member(course_id));

drop function public.is_course_member(integer);

commit;
