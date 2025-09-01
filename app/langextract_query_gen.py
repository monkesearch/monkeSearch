#!/usr/bin/env python3
import langextract as lx
import textwrap

class QueryExtractor:
    def __init__(self, model_id="file:Qwen3-0.6B-Q4_K_M.gguf"):
        self.config = lx.factory.ModelConfig(
            model_id=model_id,
            provider="LlamaCppLanguageModel",
            provider_kwargs=dict(
                n_gpu_layers=-1,
                n_ctx=0,
                verbose=True,
                
            ),
        )
        # Shortened prompt
        self.prompt = textwrap.dedent("""\
                                      /no_think
            Extract from search queries:
            
            FILE TYPES: Include extensions and set specific=true for exact types (pdf, mp4), false for categories (images, documents).
            
            TEMPORAL: Only extract explicit numeric values from the past.
            - time_unit: days, weeks, months, years
            - value: numeric only""")
        
        # Reduced examples to fit context
        self.examples = [
            lx.data.ExampleData(
                text="python scripts from 3 days ago",
                extractions=[
                    lx.data.Extraction(
                        extraction_class="file_type_indicator",
                        extraction_text="python scripts",
                        attributes={"probable_extensions": "py", "specific": "true"}
                    ),
                    lx.data.Extraction(
                        extraction_class="temporal_indicator",
                        extraction_text="3 days ago",
                        attributes={"time_unit": "days", "value": "3"}
                    ),
                ]
            ),
            lx.data.ExampleData(
                text="photos from yesterday",
                extractions=[
                    lx.data.Extraction(
                        extraction_class="file_type_indicator",
                        extraction_text="photos",
                        attributes={"probable_extensions": "jpg,png", "specific": "false"}
                    ),
                    lx.data.Extraction(
                        extraction_class="temporal_indicator",
                        extraction_text="yesterday",
                        attributes={"time_unit": "days", "value": "1"}
                    ),
                ]
            ),
            lx.data.ExampleData(
                text="pdf files",
                extractions=[
                    lx.data.Extraction(
                        extraction_class="file_type_indicator",
                        extraction_text="pdf",
                        attributes={"probable_extensions": "pdf", "specific": "true"}
                    ),
                ]
            )
        ]
    
    def extract(self, query):
        """Extract file types and temporal indicators from query"""
        result = lx.extract(
            config=self.config,
            text_or_documents=query,
            prompt_description=self.prompt,
            examples=self.examples,
            fence_output=False,
            use_schema_constraints=False,
            max_char_buffer=50,  # Reduced buffer
            extraction_passes=1,
            max_workers=1,  # Reduced workers
        )
        
        return result
    
    def get_file_types(self, query):
        """Extract only file types from query"""
        result = self.extract(query)
        file_types = []
        extracted_text = []
        
        if result and result.extractions:
            for extraction in result.extractions:
                if extraction.extraction_class == "file_type_indicator":
                    extensions = extraction.attributes.get("probable_extensions", "")
                    file_types.extend([ext.strip() for ext in extensions.split(",")])
                    extracted_text.append(extraction.extraction_text)
        
        return file_types, extracted_text
    
    def get_temporal(self, query):
        """Extract only temporal indicators from query"""
        result = self.extract(query)
        temporal_data = []
        extracted_text = []
        
        if result and result.extractions:
            for extraction in result.extractions:
                if extraction.extraction_class == "temporal_indicator":
                    temporal_data.append({
                        "text": extraction.extraction_text,
                        "time_unit": extraction.attributes.get("time_unit"),
                        "value": extraction.attributes.get("value")
                    })
                    extracted_text.append(extraction.extraction_text)
        
        return temporal_data, extracted_text
    
    def parse_query(self, query):
        """Parse query and return structured data"""
        
        # Simplified stop words
        STOP_WORDS = {'the', 'a', 'an', 'find', 'search', 'file', 'files'}
        words = query.split()
        filtered_words = [word for word in words if word.lower() not in STOP_WORDS]
        cleaned_query = " ".join(filtered_words)
        
        result = self.extract(cleaned_query)
        
        file_types = []
        temporal_data = []
        all_extracted_text = []
        is_specific = False
        
        if result and result.extractions:
            for extraction in result.extractions:
                if extraction.extraction_class == "file_type_indicator":
                    extensions = extraction.attributes.get("probable_extensions", "")
                    file_types.extend([ext.strip() for ext in extensions.split(",")])
                    all_extracted_text.append(extraction.extraction_text)
                    if extraction.attributes.get("specific", "false") == "true":
                        is_specific = True
                    
                elif extraction.extraction_class == "temporal_indicator":
                    temporal_data.append({
                        "text": extraction.extraction_text,
                        "time_unit": extraction.attributes.get("time_unit"),
                        "value": extraction.attributes.get("value")
                    })
                    all_extracted_text.append(extraction.extraction_text)
        
        # Get remaining text (misc keywords)
        misc_keywords = cleaned_query
        for text in all_extracted_text:
            misc_keywords = misc_keywords.replace(text, "").strip()
        
        if misc_keywords:
            words = misc_keywords.split()
            filtered_words = [word for word in words if len(word) > 2]
            misc_keywords = " ".join(filtered_words)
        
        return {
            "file_types": file_types,
            "temporal": temporal_data,
            "misc_keywords": misc_keywords,
            "is_specific": is_specific,
            "original_query": query
        }


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser()
    parser.add_argument("query", type=str)
    args = parser.parse_args()
    
    extractor = QueryExtractor()
    parsed = extractor.parse_query(args.query)
    
    print(f"File types: {parsed['file_types']}")
    print(f"Temporal: {parsed['temporal']}")
    print(f"Misc keywords: {parsed['misc_keywords']}")
    print(f"Is specific: {parsed['is_specific']}")