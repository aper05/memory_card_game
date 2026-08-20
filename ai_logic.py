import random

class AIPlayer:
    def __init__(self, difficulty='easy', smartness=50):
        self.difficulty = difficulty
        self.smartness = smartness / 100.0   # 0.0 to 1.0

        if difficulty == 'easy':
            self.memory_size = 2
            self.smartness = 0.4
        elif difficulty == 'medium':
            self.memory_size = 4
            self.smartness = 0.6
        else:  # hard
            self.memory_size = 8
            self.smartness = 0.9

        self.recent_memory = []

    def update_memory(self, revealed_cards):
        """ revealed_cards: iterable of (index, face_id) that were just revealed """
        for idx, face_id in revealed_cards:
            
            self.recent_memory = [entry for entry in self.recent_memory if entry[0] != idx]
            self.recent_memory.append((idx, face_id))
        
        while len(self.recent_memory) > self.memory_size:
            self.recent_memory.pop(0)

    def _get_unknown_cards(self, board):
        return [i for i, card in enumerate(board.cards)
                if not card.is_matched and not card.is_flipped]

    def _get_unseen_unknown_cards(self, board):
        unknown = self._get_unknown_cards(board)
        seen_indices = {entry[0] for entry in self.recent_memory}
        return [i for i in unknown if i not in seen_indices]

    def get_first_card(self, board):
        unknown = self._get_unknown_cards(board)
        if not unknown:
            return None

        use_memory = random.random() < self.smartness

        if use_memory and self.recent_memory:
            face_to_indices = {}
            for idx, face in self.recent_memory:
                if idx in unknown and not board.cards[idx].is_matched:
                    face_to_indices.setdefault(face, []).append(idx)
            for face, indices in face_to_indices.items():
                if len(indices) >= 2:
                    for idx in indices:
                        if idx in unknown:
                            return idx
            unseen = self._get_unseen_unknown_cards(board)
            if unseen:
                return random.choice(unseen)
            return random.choice(unknown)
        else:
            unseen = self._get_unseen_unknown_cards(board)
            if unseen:
                return random.choice(unseen)
            return random.choice(unknown)

    def get_second_card(self, board, first_idx):
        first_face = board.cards[first_idx].face_id
        unknown = self._get_unknown_cards(board)

        use_memory = random.random() < self.smartness

        if use_memory:
            for idx, face in self.recent_memory:
                if idx != first_idx and face == first_face and idx in unknown:
                    return idx

        unseen = self._get_unseen_unknown_cards(board)
        if first_idx in unseen:
            unseen.remove(first_idx)
        if unseen:
            return random.choice(unseen)

        unknown_copy = unknown[:]
        if first_idx in unknown_copy:
            unknown_copy.remove(first_idx)
        if not unknown_copy:
            return None
        return random.choice(unknown_copy)