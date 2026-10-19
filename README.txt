THE FORGE  |  Copyright (c) 2026 Yannie D. Forest. All rights reserved.
NO LICENCE IS GRANTED. No copying, adaptation, redistribution, reverse
engineering or commercial use without the author's written permission.
See LICENCE.txt. Every distributed copy carries a build marker.
--------------------------------------------------------------------------

THE FORGE ON A WINDOWS PC
=========================

Build 640 (9s72), 2026-10-19. Made by The Forge, 19 October 2026.

New in 640. The Carpe Diem it carries is 1057, whose mini Forge is now
The Forge 639 (it was 629) and opens on the Carpe Diem it lives in each
time, editing Carpe Diem alone. The full page carries Ingenium 5.7,
Carpe Diem 1057 and Inkwell 7.48. Nothing else in the Forge changes.

New in 639, the build before. Fabrica, your own GitHub, now stands in the Forge, on the
rail between Files and the Workshop, and it needs no model and no
connection. Each of your apps is kept as a real git repository on the
device: every version, the changes file by file and line by line, ideas
as branches brought back into main, releases, and an undo that adds a
version and never writes over one. Files are written in Fabrica's own
file editor, or in the Forge's Editor, whose edits come back as changes
to keep. A version is tested (five checks in a quiet window) and made as
one page, as a web app, or as the Forge's five install packages; any git
opens the folder, the bundle or the zip it saves, and GitHub is a switch
you turn on only if you want it. The full page carries Ingenium 5.6, in
which Decode a message and Draft a reply open a conversation of their
own, with Carpe Diem 1056 and Inkwell 7.48.

New in 638. Its Tabula lays out a long document as Word does: a
paragraph that meets the foot of a page runs on to the next one, so no
page ends in a blank gap, and a footnote is placed in a moment, even in
a thesis (Inkwell 7.45's recipe). Footnotes stand at the foot of the
page that cites them, are written where they stand, and go into Word
files as real footnotes (Inkwell 7.48's recipe). Tabula keeps its
raised pages when it is opened on its own. There is more room on the
device: Tabula autosaves a document of up to 256 MB in the browser's
larger store, and when the small store (about 5 MB) is full, the
Forge's desk is kept in the larger store and opens from there. It
carries Ingenium 5.5 (which brings in your Claude conversations),
Carpe Diem 1056 and Inkwell 7.48.

New in 637. The help level keys ("First day", "Finding my way",
"At ease") are raised and move like every other key in the Forge: they
lift under the pointer, sink when pressed, and the chosen level is the
filled key, which settles into place. They follow day, night and the
Forge's Minimal motion setting. It carries the same apps as 636:
Ingenium 5.4, Carpe Diem 1055 and Inkwell 7.45.

New in 636. It carries Inkwell 7.45, which adds the checks a
doctoral editor makes on the whole document, places Chicago footnotes in
a third of a second, and runs long paragraphs on across pages. It
carries Carpe Diem 1055, whose Tabula holds a thesis of 100,000 words and
whose mini Forge edits Carpe Diem alone, and Ingenium 5.4, which carries
both, and a copy of itself. The Mac app in every kit the Forge makes now
builds on GitHub: its first start as Intel, under Rosetta, may take up to
40 seconds before the build counts it as failed (it was 12).

New in 635. Its own Tabula now holds a thesis of 100,000 words, by
Inkwell 7.44's recipe. A keystroke is answered at once, because the
pages are laid out only as far as an edit moves them. A long document is
kept in the browser's larger store (IndexedDB), so it is not lost when it
outgrows the small one. It carries Inkwell 7.44, whose Tabula opens and
keeps such a thesis, finds anything in it as Word's Navigation pane does,
and offers eleven supports for your own way of working, each off until
you switch it on. It also carries Ingenium 5.3, whose Tabula holds a
thesis by the same recipe and whose Lector keeps the figures of an
edition you keep outside it (such as a full edition) apart from the copy
it carries, and Carpe Diem 1054, and a copy of itself.

New in 634, the build before. It carries Ingenium 5.2, whose Lector now keeps your
documents true to each new build: it measures your apps on your device,
finds every figure an update changed in your own words, and updates your
Word files in place, keeping each version. It also carries Carpe Diem 1054
and Inkwell 7.43, and a copy of itself.

New in 633, the build before. The tour and the Guidebook describe the workshop as it now
stands: nine rooms on the rail in four groups, the Editor's five steps, and
new cards for Files, Focus, the Inbox (the thought bubble), the Agenda and
Projects, in English and French. The tour's Editing switch card rings the
switch where it now is, and says that the Forge carries its apps inside it.
Magister's tip and the Guidebook now say four questions for each module, as
the Assessments room has them, and year 1, term 1 is said to hold eight
lessons, as it does. The lesson shown after the carried apps are kept names
the fingerprints they were checked against. It carries Ingenium 5.1,
Carpe Diem 1054 and Inkwell 7.43, and a copy of itself.

New in 632, the build before. The Forge carries your four apps inside this one file, as
Ingenium does: Ingenium 5.0, Carpe Diem 1052 and Inkwell 7.43, and a copy of
itself. On its first start on each device it keeps them in the Editor, each
checked against its fingerprint, so no app library file is needed any more.
The copies it carries are lean: Ingenium comes without the apps Ingenium
carries, and the Forge's copy of itself without the apps the Forge carries
(a file cannot hold a full copy of an app that holds a full copy of it back).
The thoughts panel now follows day and night while it is open, and the Focus
room uses the newest support module.

Since 631. The Forge has its own supports, the same ones Carpe Diem has, all
inside this one file: a thought-bubble side button under the bell, with a
light raised thoughts panel you can drag and resize from any edge (the minus
key puts words away and the bubble reminds you; the cross asks before letting
them go), a count of what waits, gentle reminders that take turns between the
parts of your life, and a Focus room at the head of the day's group on the
rail: Now, Steps, Time, the Inbox, Calm, Routines, Today in the Forge, and a
switch for each support. The live preview no longer shakes while the Editor
scrolls: its height is now measured from the page itself, not from where the
page has scrolled to.

On Windows, The Forge is one standalone program. You install it once
with its installer. Then it opens in its own window from the Start menu,
like any other program. It needs nothing else on your PC: no Python, and
no browser.

The installer is made for you on GitHub, the same way Inkwell's is. This
package holds what GitHub needs to make it.

Like Inkwell, The Forge draws its own window with Microsoft's WebView2
component, which comes with Windows 10 and 11. That is not a browser
window.

WHAT IS IN THIS PACKAGE
  READ ME FIRST.txt               This guide.
  Windows project\                Everything GitHub needs to build the
                                  program and its installer.
  GITHUB_WORKFLOW_paste_this.txt  The build recipe, as a visible file you can
                                  copy from (Part 1, Step 3).
  LICENCE.txt

WHAT IS NEW IN THIS BUILD
  - The program is built the way Inkwell is built, with the same
    ready-made starter that Inkwell has. (A starter is the small part
    that opens a program. Earlier builds made a new one each time.)
  - There is one way to have The Forge on Windows: the installer from
    your Releases page. The two .bat files are gone; they needed Python
    on the PC.
  - GitHub's check with Microsoft Defender now only scans. It no longer
    changes any of Defender's settings, and this package carries no
    such commands.
  - If The Forge ever closes unexpectedly, it still opens in its own
    window next time. It never opens your browser by itself for that.


PART 1. HAVE GITHUB MAKE THE INSTALLER
--------------------------------------

Step 1. Make a repository.
  Sign in at github.com. Click the "+" at the top right, then
  "New repository". Name it, for example the-forge-windows. Choose
  Private. Do NOT tick "Add a README file". Click "Create repository".
  (You may use the repository you already have for this app instead.)

Step 2. Upload the project.
  On the new repository's page click "uploading an existing file".
  Open the folder "Windows project" from this package, select EVERYTHING
  INSIDE IT (Ctrl+A), and drag it onto the page. You should see
  the_forge.spec, the_forge.iss, the_forge_app.py and
  the_forge.html in the list. Wait until every file has finished
  uploading, then click "Commit changes".
  If your repository still holds the two .bat files from an older
  package, they are no longer used. You may leave them or delete them.

Step 3. Add the build recipe. THIS STEP MATTERS.
  The recipe lives in a folder called .github, which is easily left
  behind when uploading (a Mac always hides it). Without it GitHub
  never builds anything.
    a. On the repository page click "Add file", then "Create new file".
    b. In the name box type exactly:
           .github/workflows/build-windows-app.yml
       (GitHub turns each "/" into a folder as you type.)
    c. Open GITHUB_WORKFLOW_paste_this.txt from this package, select all
       of it, copy it, and paste it into the large box on GitHub.
    d. Click "Commit changes", then "Commit changes" again.
  If GitHub says the file already exists, it uploaded in Step 2. If you
  are updating a repository that had an OLDER recipe, open the file
  there, click the pencil, replace everything with the new text, and
  commit.

Step 4. Wait for the build.
  Click the "Actions" tab. "Build The Forge for Windows" runs for about
  five to ten minutes; a green tick means it worked.
  On GitHub's own Windows computer it:
    - builds the program as a program folder, with PyInstaller's
      standard starter (as Inkwell's) and its version details;
    - checks that the app inside is byte for byte the file the_forge.html
      you uploaded;
    - opens it, waits until its page says it is ready (at most two
      minutes), and notes how long that took. It keeps a photograph of
      it under "Artifacts", and tries a second start, which should only
      bring the open window to the front (a warning if it does not);
    - makes the installer, then installs and uninstalls it silently,
      also over the open program and while it is open;
    - scans the installer and the program with Microsoft Defender,
      with the newest definitions. It only scans: it changes nothing in
      Defender. If Defender names a threat, the run stops with a red
      cross and NOTHING is published.
  If nothing has started after a minute: click "Build The Forge for
  Windows" on the left, then "Run workflow", then the green "Run workflow".

Step 5. Get the installer.
  On the repository's main page, on the right, click "Releases", then
  the release named "The Forge ... for Windows (build ...)". Its name
  gives the version and the build number. Under "Assets", the installer
  is the file whose name ends in "-Setup.exe". It is the only file to
  download.
  The release notes say what Microsoft Defender found on GitHub's
  computer (nothing, or "NOT MEASURED" if it could not scan there),
  which starter the program was built with, how long the program took
  to open there, and the installer's SHA-256 fingerprint.

COST: for a private repository GitHub counts each minute on its Windows
computers as more than one minute of your monthly allowance (twice, as
far as I know). One build takes about five to ten minutes. Please check
GitHub's current figures on its billing pages.


PART 2. INSTALL THE FORGE
-------------------------

1. If you already use The Forge on this PC, export a backup from it
   first and keep the file (in The Forge: Settings, Backup, "Export
   everything"). The installer also copies the folder that holds your
   work before it changes anything.
2. Download the installer from the Releases page (Part 1, Step 5).
   Microsoft Edge may warn that the file is not commonly downloaded.
   That warning is about reputation: the file is new, few people have
   downloaded it yet, and it is not signed with a paid certificate. It
   is not about anything found inside it. Do NOT click "Delete":
     a. Point at the download and click the three dots beside it.
     b. Click "Keep".
     c. Click "Show More", then "Keep anyway".
   If Edge says instead that the file may be unwanted or unsafe, that
   is Microsoft's judgement of the file itself. Please follow IF WINDOWS
   REMOVES IT, below, before you keep it.
3. Open the installer. The first time, Windows may show "Windows
   protected your PC".
     a. Click the small link under the message (as far as I know it
        says "More info").
     b. Click "Run anyway".
   This too is about reputation (CODE SIGNING, below). You see it once
   for each new installer.
4. The installer needs no administrator password. It installs
   The Forge for you only, into %LOCALAPPDATA%\Programs\The Forge,
   puts it in the Start menu, and on the Desktop if you leave that box
   ticked. Click Install. At the end it offers to open The Forge.
5. If the OLD single file The Forge.exe, or The-Forge-Windows.zip, is still
   on your Desktop or in Downloads, delete it. Your work is not inside
   it.

The installed program is a folder: The Forge.exe and, beside it, a
folder named _internal. Keep them together, and open The Forge from
the Start menu or the Desktop shortcut.

To remove The Forge: Settings, Apps, Installed apps, The Forge,
Uninstall. Your work stays in %LOCALAPPDATA%\TheForge. If The Forge
is open, the uninstaller first closes it, the way its own close button
does.

WebView2 is on nearly every Windows 10 and 11 PC. If it is missing, the
installer says so on one page, with a button to Microsoft's free
download, and carries on. Install "Microsoft Edge WebView2 Runtime" from
that page, then open The Forge. Until then it cannot draw its own
window; it opens in your browser instead, and says so.


IF WINDOWS REMOVES IT, OR CALLS IT MALWARE OR UNWANTED
------------------------------------------------------
Of Windows' guards, only Microsoft Defender Antivirus (part of Windows
Security) removes a file. Edge's warnings, "Windows protected your PC"
and Smart App Control warn or block, but do not delete.

Each time Defender removes something, Windows keeps a note. The note
says what Windows thought it found, and which file. With that, the
right thing can be fixed. Windows keeps these notes for a short time
only (about two weeks, as far as I know), so it helps to look soon.

Find the exact name:
  1. Click Start, type Windows Security, and open it.
  2. Choose "Virus & threat protection".
  3. Under "Current threats", choose "Protection history".
  4. Find the entry from the day The Forge disappeared, and click it
     to open it. If Windows asks for permission, choose Yes.
  5. Write down, or photograph, three things:
       - the name of the threat (it may begin with a word such as
         "Trojan" or "PUA", and it may end with "!" and two letters);
       - the file it names, with its folder (a line beginning C:\);
       - what Windows did, and the date.
  6. Please do not press "Allow" or "Restore" yet. Nothing changes
     until you choose, and we can decide together once the name is
     known.
  7. Go back to "Virus & threat protection", choose "Protection
     updates", and note the "Security intelligence" version (as far as
     I know it is shown there).
  8. Pass the photo or the notes on. That is all.

If the entry has gone, Event Viewer usually keeps the same facts for
longer (as far as I know):
  1. Press the Windows key and R together, type eventvwr.msc, and press
     OK.
  2. On the left, open "Applications and Services Logs", then
     "Microsoft", "Windows", "Windows Defender", "Operational".
  3. Look for events numbered 1116 and 1117 on the day The Forge
     disappeared, and click one.
  4. Note or photograph "Name" (the threat), "Path" (the file) and
     "Signature Version" (the definitions).

If neither shows anything, the stop may have come from SmartScreen or
Smart App Control instead. Next time, note the words on the screen, or
take a picture of the screen with the Windows key, Shift and S together.

What the name says. Its first word gives the kind of judgement:
"Trojan" and similar words mean Defender judged the file harmful; "PUA"
or "App" means a "potentially unwanted app". A name ending in "!ml" is
common for a new program. Microsoft does not say what "!ml" means; it is
widely read as "machine learning", a guess that the file looks like
harmful ones, not a match with any known harmful program.

Report the mistake to Microsoft (free). Microsoft's page for this is
"Submit a file for malware analysis":
    https://www.microsoft.com/en-us/wdsi/filesubmission
  1. Open that page. For "Submit file as a", choose "Software
     developer".
  2. Sign in with a Microsoft account. That is how you see Microsoft's
     answer.
  3. Choose the product that removed it, for example "Microsoft
     Defender Antivirus (Windows 11)".
  4. Choose the file: the exact file Protection history named (for
     example the installer, whose name ends in "-Setup.exe"). The page
     takes files up to 50 MB.
  5. For "What do you believe this file is?", choose "Incorrectly
     detected as malware/malicious". If the name began with "PUA",
     choose "Incorrectly detected as PUA (potentially unwanted
     application)" instead.
  6. "Detection name": copy the name exactly from Protection history.
  7. "Definition version": the Security intelligence version you noted.
  8. "Additional information", in English: say that this is your own
     offline desktop program, built with PyInstaller and Inno Setup on
     GitHub from your own repository, and paste the SHA-256 given in the
     release notes.
  9. Send it, and wait for Microsoft's answer. When Microsoft agrees, it
     changes its definitions. Then, in Windows Security, choose "Virus &
     threat protection", "Protection updates", "Check for updates", and
     download and install The Forge again.

Please do not switch Defender off, and do not exclude whole folders such
as Downloads.

If the message names Smart App Control, there is no "Run anyway". Smart
App Control (Windows 11) blocks an unsigned program unless Microsoft's
cloud already trusts it. It can be switched off in Windows Security,
"App & browser control", "Smart App Control settings". Microsoft's own
pages disagree on whether it can be switched on again later without
resetting Windows, so please think it over first.


WHY WINDOWS MAY HAVE REMOVED IT
-------------------------------
We do not know yet which file Windows removed, or the name it gave. The
steps above find both. What we do know:
  - Inkwell is made the same way The Forge now is, and your laptops
    accept it.
  - Until this build, the main difference in The Forge's program was
    its starter: a new one was made for every build, so Windows had never
    seen it before. It now has the same ready-made starter as Inkwell.
  - GitHub's scan is good evidence, not a guarantee. Your PC can also
    ask Microsoft's cloud, and may send it a new program for a closer
    look. The cloud may judge differently. If it does, the steps above
    say what to do.


CODE SIGNING: THE ONLY CURE FOR THE WARNINGS, AND IT COSTS MONEY
----------------------------------------------------------------
Neither Inkwell nor The Forge is signed today. Code signing attaches
your verified name to every build. Windows then names you as the
publisher, Smart App Control lets the program run, and SmartScreen's
trust carries over from one build to the next, so the warnings fade as
people install it. It does not promise that Defender never objects; for
that, the report above is the cure.

Signing needs either Microsoft's own signing service (a monthly fee; as
far as I know open to individual developers only in the United States
and Canada) or a code-signing certificate from a certificate authority (a
yearly fee, with the key kept on a hardware token or in the authority's
cloud). Please check the current prices and conditions with the
providers. The free signing programmes I know of are for open-source
projects only, and The Forge is not open source. Once you have a
signing account, the GitHub build can be extended to sign every build
automatically.


PART 3. UPDATING THE PROGRAM LATER
----------------------------------

  1. On GitHub, open your repository. Click "Add file", then "Upload
     files", drop in EVERYTHING inside the new package's "Windows
     project" folder (the app, its icon, BUILD_INFO.txt and the rest;
     the files replace the old ones), and commit.
  2. GitHub builds again by itself (Part 1, Steps 4 and 5).
  3. Download the new installer and open it. It replaces the program and
     keeps your work.


IF THE BUILD FAILS
------------------

A red cross within a few seconds, with no steps listed:
  GitHub refused to start the build. This is about the GitHub account,
  not the app. Open the failed run and read the notice near the top.
  The usual reasons are that the account has used its monthly free
  minutes, or a spending limit or payment problem in the billing
  settings (github.com/settings/billing). Fix what the notice names,
  then click "Re-run all jobs".

A red cross after some minutes, with steps listed:
  Click the step with the red cross. "If the build failed, show why"
  prints the last 80 lines of the build log; they name the cause.

A red cross at "Scan with Microsoft Defender":
  Defender named a threat, so nothing was published. The step's text,
  and defender-report.txt under "Artifacts", name the file and the
  threat. Report it to Microsoft as described above, then run the build
  again once Microsoft has answered. Please do not remove the scan.

A yellow warning that Defender was "not measured":
  GitHub's computer could not run the scan this time. The installer was
  published, and its release notes say "NOT MEASURED".

A red cross at "Put the installer on the Releases page":
  First click "Re-run failed jobs". GitHub's upload service sometimes
  fails (for example "HTTP 500"), and the recipe already tries four
  times. Only if the message says 403 or "Resource not accessible by
  integration": Settings, Actions, General, Workflow permissions: choose
  "Read and write permissions", Save, then "Re-run all jobs".

"the_forge.spec not found" or "the_forge.iss is missing":
  The project was not uploaded, or only partly. Upload the CONTENTS of
  "Windows project" again (Part 1, Step 2).


ABOUT THE PROGRAM
-----------------
  - It runs entirely from the copy of the_forge.html inside it and works with
    no connection. Your work is kept in this folder on the PC:
        %LOCALAPPDATA%\TheForge
    and the installer copies it to %LOCALAPPDATA%\TheForge\backups
    before each installation, keeping the three newest copies.
  - Only one copy opens at a time. If you click its icon again while it
    is open, or still opening, its window comes to the front. No second
    copy starts.
  - The window opens in the colour of the page, light or dark, as you
    last used it.
  - Each build measures how long the program takes to open on GitHub's
    Windows computer. The release notes give the times: window shown,
    page loaded, page ready. That computer has no graphics chip, so a PC
    is usually quicker.
  - It always opens in its own window. If a run ever ends badly (for
    example the PC loses power while it is open), the next run switches
    to safe graphics on that PC: a little less smooth, and steadier. A
    small note, the_forge_safe_graphics.txt in
    %LOCALAPPDATA%\TheForge\storage, says so. To try full graphics
    again, close The Forge and delete that note.
  - It writes a short record of each start to the_forge_crash.log, in
    %LOCALAPPDATA%\TheForge. If something goes wrong, that file says
    what happened.
