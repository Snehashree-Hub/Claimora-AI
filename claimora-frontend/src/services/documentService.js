import { analyzeClaimReadiness } from "./api";

export async function verifyDocuments(files) {
  const formData = new FormData();

  for (const file of files) {
    formData.append("files", file);
  }

  return analyzeClaimReadiness(formData);
}
