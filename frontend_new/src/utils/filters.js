/** Map sidebar filter state to API body fields (omit "All"). */
export function filterPayload(filters) {
  const body = {};
  if (filters?.topic && filters.topic !== 'All') body.topic = filters.topic;
  if (filters?.docType && filters.docType !== 'All') body.doc_type = filters.docType;
  return body;
}
