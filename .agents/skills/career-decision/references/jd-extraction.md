# JD Extraction

Use the JD schema's exact field names. Inspect all screenshots; preserve original text and language. Capture employer/agency distinction, role, duties, qualifications, employment, compensation, benefits, location, dates, and other visible conditions. Ignore platform controls and unrelated overlays.

For each item retain jd_item_id, section, exact_text, source_ids, uncertain, and source-specific anchors. Merge repeated overlap without losing source links. Differing requirements must remain separate. A cropped source supports only its visible content; another complete source may support the full item.

Per image record readability as Complete, Partial, or Unreadable, with issues. Record unreadable_regions and mark uncertain text locally. Use Unknown for missing company/title. Do not reconstruct truncated words, invent confidence percentages, or use typical JDs to fill gaps.

Review completeness against every visible duty and qualification, including footnotes and contract terms. Ask for missing source regions only when necessary for the requested analysis; otherwise pass the extraction limitations downstream.
