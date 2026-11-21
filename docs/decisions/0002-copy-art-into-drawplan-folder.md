# 0002: Copy saved art into a drawplan folder instead of storing the original path

- Status: accepted
- Date: 2026-11-21

## Decision (Y-statement)

In the context of **R5, where the user hands drawplan the path to the image they made
today and, months later, expects to see that piece next to a recent one**, facing **the
fact that the original files live wherever the user keeps them (downloads, phone sync
folders, drawing-app exports) and are often renamed, moved, edited over or deleted long
before the monthly comparison needs them**, we decided for **copying each image into a
`drawplan_art/` folder next to the data file, under a name built from date, goal, skill
and a counter, and recording that copy's name (plus the original path for reference) in
the `art` list**, and neglected **storing only the original path (no extra disk use, but
comparisons break silently when a file moves), and embedding the image bytes in the JSON
data file (one self-contained file, but it bloats the file that is rewritten on every
log and makes it unreadable)**, to achieve **a history that keeps working however the
user reorganises their own files, a folder they can browse or back up next to their
data, and a comparison page that can use simple relative image links**, accepting
**that every saved piece takes up disk space a second time, and that editing the
original later does not update drawplan's copy. That is the point of a dated record, but
it can surprise users.**
