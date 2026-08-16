export function dataURLToBlob(dataURL:string) {
  const [header, base64] = dataURL.split(",");

  const mimeMatch = header.match(/:(.*?);/);
  if (!mimeMatch) throw new Error("Invalid data URL header");
  const mime = mimeMatch[1];

  const binary = atob(base64);
  const bytes = new Uint8Array(binary.length);

  for (let i = 0; i < binary.length; i++) {
    bytes[i] = binary.charCodeAt(i);
  }

  return new Blob([bytes], { type: mime });
}