---
version: "1.0.0"
---
<!-- The version above is template-file metadata; it is not copied into the instantiated document. -->
<!-- The single source of the what-left file's shape. Lands at `<product>/docs/what_left.md`.

     MODEL-FACING: whoever writes or edits a product's what-left file reads this shape and writes the
     file fresh, so everything here may explain itself and none of it survives into the result. No
     script stamps it.

     WHAT THIS FILE OWNS: the file's body and the shape of one entry. Nothing else. What may be an
     entry, who adds one, who removes one, and how a reader reads the file are
     `<CORE>/doctrine/setup/kensaiapp_structure.md` § 3 Product, *The what-left file — the one place a
     product states what is still to build*. They are not restated here.

     THE THREE FIELD LABELS ARE EXACT: `**Wanted:**`, `**Source:**` and `**Missing at:**`. A reader
     finds an entry by matching them literally, so a renamed label is an entry no reader finds.

     ONE ENTRY HOLDS ONE WANTED THING. Repeat the entry block once per thing, with no placeholder left
     in any field.

     THE EMPTY MARKER is the line below, exactly, alone on its line. It replaces every entry when the
     last one is removed, and the file is never deleted:

         Nothing is left to build.

     A file holding the marker and an entry together is malformed, and so is a file holding neither.
     That is why the marker is shown here and not in the body. -->

# What is left to build — <product name>

Each entry names one thing <product name>'s Agari or PRD wants that its code did not do at the commit the entry names.

- **Wanted:** <one thing the product does, or one thing that is true of it, for its user or reader>
  **Source:** <Agari or PRD> § <section heading>, **<item name, where the section has named items>**
  **Missing at:** `<short SHA of a commit on main>`
