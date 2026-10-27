-- this helps postgres find matching words without reading every chunk
-- the 10000-chunk benchmark checks that the same source IDs still come back
CREATE INDEX chunks_search_text ON chunks USING gin(to_tsvector('english',text));
