export type ApiError = { detail?: string | Array<{ msg: string }> };

export async function getErrorMessage(response: Response) {
  const data = (await response.json().catch(() => ({}))) as ApiError;
  if (typeof data.detail === "string") return data.detail;
  if (Array.isArray(data.detail)) return data.detail[0]?.msg ?? "Please check your details.";
  return "Something went wrong. Please try again.";
}
