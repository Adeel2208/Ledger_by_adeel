"""Populate search indexes with existing signals."""
from app.database import SessionLocal
from app.intelligence.retrieval import get_index
from app.memory.repository import MemoryRepository

def populate_index():
    """Index all existing signals for search."""
    db = SessionLocal()
    try:
        repo = MemoryRepository(db)
        index = get_index(hybrid=True)
        
        # Get all signals
        # We need to get signals for all founders
        from app.models.founder import Founder
        founders = db.query(Founder).all()
        
        all_signal_ids = []
        all_texts = []
        all_metadata = []
        
        for founder in founders:
            signals = repo.signals_for(founder.id)
            print(f"Found {len(signals)} signals for {founder.name}")
            
            for signal in signals:
                # Create searchable text from signal
                text_parts = [
                    f"Source: {signal.source}",
                    f"Type: {signal.record_type}",
                ]
                
                # Add payload fields
                if signal.payload:
                    for key, value in signal.payload.items():
                        if isinstance(value, (str, int, float)):
                            text_parts.append(f"{key}: {value}")
                
                # Add text if available
                if hasattr(signal, 'text') and signal.text:
                    text_parts.append(signal.text)
                
                text = " | ".join(text_parts)
                
                metadata = {
                    "founder_id": founder.id,
                    "founder_name": founder.name,
                    "source": signal.source,
                    "record_type": signal.record_type,
                    "confidence": signal.confidence,
                }
                
                all_signal_ids.append(f"signal_{signal.id}")
                all_texts.append(text)
                all_metadata.append(metadata)
        
        # Upsert in batches
        if all_signal_ids:
            print(f"\nIndexing {len(all_signal_ids)} signals...")
            batch_size = 100
            for i in range(0, len(all_signal_ids), batch_size):
                batch_ids = all_signal_ids[i:i+batch_size]
                batch_texts = all_texts[i:i+batch_size]
                batch_metadata = all_metadata[i:i+batch_size]
                
                index.upsert(batch_ids, batch_texts, batch_metadata)
                print(f"Indexed batch {i//batch_size + 1}")
            
            print(f"\n✅ Successfully indexed {len(all_signal_ids)} signals")
        else:
            print("No signals found to index")
    
    finally:
        db.close()


if __name__ == "__main__":
    populate_index()
