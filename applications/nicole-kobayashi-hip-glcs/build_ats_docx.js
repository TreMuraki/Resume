// Render the ATS resume to .docx from ats-resume.md.
//
// Same ATS constraints as the PDF build: single column, one font, no tables,
// no text boxes, no headers/footers, no graphics, standard section headings.
// Section rules are paragraph bottom borders, not table hacks.
//
//   NODE_PATH=<dir containing node_modules> node build_ats_docx.js \
//       ats-resume.md Nicole-Kobayashi-Resume-ATS.docx

const fs = require("fs");
const {
  AlignmentType,
  BorderStyle,
  Document,
  Packer,
  Paragraph,
  TextRun,
} = require("docx");

const FONT = "Arial"; // metric-compatible with the PDF's Helvetica
const [, , mdPath, outPath] = process.argv;

const half = (pt) => pt * 2; // docx sizes are half-points

function runs(text, { bold = false, size = 19 } = {}) {
  // Split on **bold** spans so inline emphasis survives.
  return text
    .split(/(\*\*[^*]+\*\*)/)
    .filter((s) => s.length)
    .map((seg) => {
      const b = seg.startsWith("**") && seg.endsWith("**");
      return new TextRun({
        text: b ? seg.slice(2, -2) : seg,
        bold: bold || b,
        font: FONT,
        size: half(size),
      });
    });
}

const SECTION_RULE = {
  bottom: { style: BorderStyle.SINGLE, size: 6, color: "000000", space: 2 },
};

function build(lines) {
  const out = [];
  let i = 0;

  const nextContentLine = (from) => {
    let j = from;
    while (j < lines.length && !lines[j].trim()) j += 1;
    return j;
  };

  while (i < lines.length) {
    const line = lines[i].trim();
    i += 1;
    if (!line) continue;

    if (line.startsWith("# ")) {
      out.push(
        new Paragraph({
          children: runs(line.slice(2).trim(), { bold: true, size: 17 }),
          spacing: { after: 40 },
        })
      );
      const j = nextContentLine(i);
      if (j < lines.length && !lines[j].trim().startsWith("#")) {
        out.push(
          new Paragraph({
            children: runs(lines[j].trim(), { size: 9.5 }),
            spacing: { after: 180 },
          })
        );
        i = j + 1;
      }
      continue;
    }

    if (line.startsWith("## ")) {
      out.push(
        new Paragraph({
          children: runs(line.slice(3).trim().toUpperCase(), {
            bold: true,
            size: 10.5,
          }),
          spacing: { before: 180, after: 60 },
          border: SECTION_RULE,
        })
      );
      continue;
    }

    if (line.startsWith("### ")) {
      out.push(
        new Paragraph({
          children: runs(line.slice(4).trim(), { bold: true, size: 10 }),
          spacing: { before: 120, after: 0 },
        })
      );
      const j = nextContentLine(i);
      if (
        j < lines.length &&
        lines[j].trim() &&
        !/^[-#]/.test(lines[j].trim())
      ) {
        out.push(
          new Paragraph({
            children: runs(lines[j].trim(), { size: 9 }),
            spacing: { after: 40 },
          })
        );
        i = j + 1;
      }
      continue;
    }

    if (line.startsWith("- ")) {
      const chunk = [line.slice(2).trim()];
      while (
        i < lines.length &&
        lines[i].trim() &&
        !/^\s*[-#]/.test(lines[i]) &&
        /^[ \t]/.test(lines[i])
      ) {
        chunk.push(lines[i].trim());
        i += 1;
      }
      // A literal hyphen, not a numbering-driven glyph: ATS parsers read the
      // character in the text stream, and auto-numbering puts nothing there.
      out.push(
        new Paragraph({
          children: runs("- " + chunk.join(" "), { size: 9.5 }),
          indent: { left: 220, hanging: 220 },
          spacing: { after: 50 },
          alignment: AlignmentType.LEFT,
        })
      );
      continue;
    }

    const chunk = [line];
    while (i < lines.length && lines[i].trim() && !/^\s*[-#]/.test(lines[i])) {
      chunk.push(lines[i].trim());
      i += 1;
    }
    out.push(
      new Paragraph({
        children: runs(chunk.join(" "), { size: 9.5 }),
        spacing: { after: 60 },
      })
    );
  }

  return out;
}

const doc = new Document({
  creator: "Nicole Kobayashi",
  title: "Nicole Kobayashi - Resume",
  description: "Grant Life Cycle Specialist",
  styles: {
    default: {
      document: { run: { font: FONT, size: half(9.5) } },
    },
  },
  sections: [
    {
      properties: {
        page: {
          size: { width: 12240, height: 15840 }, // US Letter, DXA
          margin: { top: 720, right: 864, bottom: 720, left: 864 },
        },
      },
      children: build(fs.readFileSync(mdPath, "utf8").split(/\r?\n/)),
    },
  ],
});

Packer.toBuffer(doc).then((buf) => {
  fs.writeFileSync(outPath, buf);
  console.log(`wrote ${outPath}`);
});
