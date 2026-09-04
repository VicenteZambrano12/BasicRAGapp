const escapePdfText = (text) =>
  text.replace(/\\/g, '\\\\').replace(/\(/g, '\\(').replace(/\)/g, '\\)');

const createPdf = (lines) => {
  const byteLength = (value) => new TextEncoder().encode(value).length;
  const content = [
    'BT',
    '/F1 22 Tf',
    '50 760 Td',
    `(${escapePdfText(lines[0])}) Tj`,
    '/F1 11 Tf',
    '0 -32 Td',
    ...lines.slice(1).flatMap((line) => [
      `(${escapePdfText(line)}) Tj`,
      '0 -20 Td',
    ]),
    'ET',
  ].join('\n');

  const objects = [
    '<< /Type /Catalog /Pages 2 0 R >>',
    '<< /Type /Pages /Kids [3 0 R] /Count 1 >>',
    '<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>',
    '<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>',
    `<< /Length ${byteLength(content)} >>\nstream\n${content}\nendstream`,
  ];

  let pdf = '%PDF-1.4\n';
  const offsets = [0];
  objects.forEach((object, index) => {
    offsets[index + 1] = byteLength(pdf);
    pdf += `${index + 1} 0 obj\n${object}\nendobj\n`;
  });

  const xrefOffset = byteLength(pdf);
  pdf += `xref\n0 ${objects.length + 1}\n0000000000 65535 f \n`;
  offsets.slice(1).forEach((offset) => {
    pdf += `${String(offset).padStart(10, '0')} 00000 n \n`;
  });
  pdf += `trailer\n<< /Size ${objects.length + 1} /Root 1 0 R >>\nstartxref\n${xrefOffset}\n%%EOF`;

  return new Blob([pdf], { type: 'application/pdf' });
};

export const createHowItWorksPdfUrl = (translations) => {
  const lines = [
    translations.pdfTitle,
    '',
    translations.pdfIntro,
    '',
    `1. ${translations.pdfStepOne}`,
    `2. ${translations.pdfStepTwo}`,
    `3. ${translations.pdfStepThree}`,
    `4. ${translations.pdfStepFour}`,
    '',
    translations.pdfStack,
  ];
  return URL.createObjectURL(createPdf(lines));
};