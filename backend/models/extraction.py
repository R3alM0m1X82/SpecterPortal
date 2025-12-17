"""
Extraction metadata model for tracking token imports
"""
from datetime import datetime
from database import db


class ExtractionMetadata(db.Model):
    __tablename__ = 'extraction_metadata'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    target = db.Column(db.String(255), nullable=True)
    extraction_time = db.Column(db.DateTime, nullable=True)
    extraction_method = db.Column(db.String(100), nullable=True)
    tokens_count = db.Column(db.Integer, default=0)
    imported_at = db.Column(db.DateTime, default=datetime.utcnow)
    source_file = db.Column(db.String(255), nullable=True)
    
    def __repr__(self):
        return f'<ExtractionMetadata {self.id}: {self.target} ({self.tokens_count} tokens)>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'target': self.target,
            'extraction_time': self.extraction_time.isoformat() if self.extraction_time else None,
            'extraction_method': self.extraction_method,
            'tokens_count': self.tokens_count,
            'imported_at': self.imported_at.isoformat() if self.imported_at else None,
            'source_file': self.source_file
        }
